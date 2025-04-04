import logging
import base64
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class MailMail(models.Model):
    _inherit = 'mail.mail'
    
    # Add flag to track if we already tried Graph API
    graph_api_attempted = fields.Boolean('Graph API Attempted', default=False, copy=False)
    
    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
        """Override to use Microsoft Graph API if enabled"""
        _logger.info("=== MAIL_GRAPH_API: mail.mail._send method called for mail IDs %s ===", self.ids)
        
        # Group emails by mail server
        mail_by_server = {}
        mail_without_server = []
        
        for mail in self:
            if mail.graph_api_attempted:
                _logger.info("=== MAIL_GRAPH_API: Mail ID %s already attempted with Graph API, using standard method ===", mail.id)
                mail_without_server.append(mail.id)
                continue
                
            if mail.mail_server_id:
                mail_by_server.setdefault(mail.mail_server_id.id, []).append(mail.id)
            else:
                mail_without_server.append(mail.id)
        
        # For emails without server, search for Graph API enabled server
        if mail_without_server:
            graph_server = self.env['ir.mail_server'].sudo().search([('use_graph_api', '=', True)], order='sequence', limit=1)
            if graph_server:
                _logger.info("=== MAIL_GRAPH_API: Found Graph API server ID %s for %s emails ===", 
                            graph_server.id, len(mail_without_server))
                # Assign this server to all emails without server
                self.env['mail.mail'].browse(mail_without_server).write({'mail_server_id': graph_server.id})
                mail_by_server.setdefault(graph_server.id, []).extend(mail_without_server)
                mail_without_server = []
        
        # Process all emails with Graph API
        result = True
        for server_id, mail_ids in mail_by_server.items():
            server = self.env['ir.mail_server'].browse(server_id)
            if server.use_graph_api:
                mail_batch = self.browse(mail_ids)
                try:
                    # Process each mail through Graph API
                    for mail in mail_batch:
                        # Mark as attempted to avoid infinite loops
                        mail.graph_api_attempted = True
                        
                        _logger.info("Processing mail ID %s with Graph API server ID %s", mail.id, server.id)
                        # Make sure we have a valid token
                        server.refresh_token_if_needed()
                        
                        # Get recipients
                        email_to = mail.email_to
                        email_cc = mail.email_cc
                        email_bcc = mail.email_bcc
                        
                        if not email_to and not mail.recipient_ids:
                            _logger.info("Mail %s has no recipients, setting to EXCEPTION", mail.id)
                            mail.write({'state': 'exception', 'failure_reason': 'No recipient specified'})
                            continue
                        
                        # Prepare the email data
                        from_email = server.ms_sender_email
                        if not from_email:
                            _logger.warning("No sender email configured on server, using company email")
                            from_email = mail.email_from or self.env.company.email
                        
                        subject = mail.subject or ''
                        
                        # Get body
                        body = mail.body_html or mail.body
                        content_type = 'HTML' if mail.body_html else 'Text'
                        
                        _logger.info("Email details - From: %s, To: %s, Subject: %s", from_email, email_to, subject)
                        
                        # Prepare the Graph API request
                        graph_url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"
                        headers = {
                            'Authorization': f'Bearer {server.ms_access_token}',
                            'Content-Type': 'application/json'
                        }
                        
                        # Prepare recipients
                        to_recipients = []
                        if email_to:
                            for email in email_to.split(','):
                                email = email.strip()
                                if email:
                                    to_recipients.append({"emailAddress": {"address": email}})
                        
                        for partner in mail.recipient_ids:
                            if partner.email:
                                to_recipients.append({"emailAddress": {"address": partner.email}})
                        
                        cc_recipients = []
                        if email_cc:
                            for email in email_cc.split(','):
                                email = email.strip()
                                if email:
                                    cc_recipients.append({"emailAddress": {"address": email}})
                        
                        bcc_recipients = []
                        if email_bcc:
                            for email in email_bcc.split(','):
                                email = email.strip()
                                if email:
                                    bcc_recipients.append({"emailAddress": {"address": email}})
                        
                        # Prepare the email payload
                        email_payload = {
                            "message": {
                                "subject": subject,
                                "body": {
                                    "contentType": content_type,
                                    "content": body
                                },
                                "toRecipients": to_recipients,
                                "from": {
                                    "emailAddress": {
                                        "address": from_email
                                    }
                                }
                            },
                            "saveToSentItems": "true"
                        }
                        
                        # Add CC recipients if any
                        if cc_recipients:
                            email_payload["message"]["ccRecipients"] = cc_recipients
                        
                        # Add BCC recipients if any
                        if bcc_recipients:
                            email_payload["message"]["bccRecipients"] = bcc_recipients
                        
                        # Add attachments if any
                        if mail.attachment_ids:
                            _logger.info("Processing %s attachments", len(mail.attachment_ids))
                            attachments = []
                            
                            for attachment in mail.attachment_ids:
                                try:
                                    attachment_data = {
                                        "@odata.type": "#microsoft.graph.fileAttachment",
                                        "name": attachment.name,
                                        "contentType": attachment.mimetype or "application/octet-stream",
                                        "contentBytes": base64.b64encode(attachment.datas).decode('utf-8')
                                    }
                                    attachments.append(attachment_data)
                                    _logger.info("Added attachment: %s", attachment.name)
                                except Exception as e:
                                    _logger.error("Failed to add attachment %s: %s", attachment.name, str(e))
                            
                            if attachments:
                                email_payload["message"]["attachments"] = attachments
                        
                        _logger.info("Sending email via Graph API")
                        
                        # Send the request to Graph API
                        import requests
                        response = requests.post(graph_url, headers=headers, json=email_payload, timeout=30)
                        _logger.info("Email sent response status: %s", response.status_code)
                        
                        if response.status_code not in [200, 202]:
                            error_message = f"Failed to send email: {response.text}"
                            _logger.error(error_message)
                            mail.write({'state': 'exception', 'failure_reason': error_message})
                        else:
                            _logger.info("Email sent successfully via Microsoft Graph API")
                            mail.write({'state': 'sent'})
                        
                        if auto_commit:
                            self.env.cr.commit()
                        
                except Exception as e:
                    _logger.error("Error sending email via Microsoft Graph API: %s", str(e), exc_info=True)
                    mail_batch.write({'state': 'exception', 'failure_reason': str(e)})
                    if raise_exception:
                        raise
                    result = False
            else:
                # Use standard method for this batch
                _logger.info("=== MAIL_GRAPH_API: Server %s does not use Graph API, using standard method for %s emails ===", 
                             server_id, len(mail_ids))
                result = result and super(MailMail, self.browse(mail_ids))._send(
                    auto_commit=auto_commit, raise_exception=raise_exception, smtp_session=smtp_session
                )
        
        # Handle remaining emails with standard method
        if mail_without_server:
            _logger.info("=== MAIL_GRAPH_API: Using standard method for %s emails without server ===", len(mail_without_server))
            result = result and super(MailMail, self.browse(mail_without_server))._send(
                auto_commit=auto_commit, raise_exception=raise_exception, smtp_session=smtp_session
            )
        
        return result
    
    @api.model
    def process_email_queue(self, ids=None):
        """Override to improve handling of Microsoft Graph API for email queue processing"""
        _logger.info("=== MAIL_GRAPH_API: process_email_queue called ===")
        
        if ids:
            _logger.info("=== MAIL_GRAPH_API: Processing specific emails: %s ===", ids)
            emails = self.browse(ids)
        else:
            # Look for emails ready to be sent
            domain = [('state', '=', 'outgoing')]
            # If a regular limit is set, respect it; otherwise, process emails in smaller batches
            limit = 50  # Process 50 emails at a time to avoid timeouts
            emails = self.search(domain, limit=limit)
            if not emails:
                return True
        
        _logger.info("=== MAIL_GRAPH_API: Found %s emails to process ===", len(emails))
        # Reset the graph_api_attempted flag to ensure we can try again with graph API
        emails.write({'graph_api_attempted': False})
        
        # Process emails with auto-commit to avoid long transactions
        return super(MailMail, emails).process_email_queue(ids=emails.ids) 