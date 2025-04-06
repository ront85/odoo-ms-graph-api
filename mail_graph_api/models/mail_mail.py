import logging
import base64
import requests
from requests.exceptions import Timeout, RequestException
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class MailMail(models.Model):
    _inherit = 'mail.mail'
    
    # Add flag to track if we already tried Graph API
    graph_api_attempted = fields.Boolean('Graph API Attempted', default=False, copy=False)
    
    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        """Override to reset the graph_api_attempted flag when manually resending emails"""
        # Reset the flag for outgoing emails when manually sending
        outgoing = self.filtered(lambda mail: mail.state == 'outgoing')
        if outgoing:
            outgoing.sudo().write({'graph_api_attempted': False})
        
        return super(MailMail, self).send(
            auto_commit=auto_commit,
            raise_exception=raise_exception,
            post_send_callback=post_send_callback
        )
    
    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        """Override to use Microsoft Graph API if enabled"""
        _logger.info("mail.mail._send method called for mail IDs %s", self.ids)
        
        if not self.ids:
            return True
        
        # Group emails by mail server
        mail_by_server = {}
        mail_without_server = []
        
        for mail in self:
            if mail.graph_api_attempted:
                _logger.info("Mail ID %s already attempted with Graph API, using standard method", mail.id)
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
                _logger.info("Found Graph API server ID %s for %s emails", 
                            graph_server.id, len(mail_without_server))
                # Assign this server to all emails without server
                self.env['mail.mail'].sudo().browse(mail_without_server).write({'mail_server_id': graph_server.id})
                mail_by_server.setdefault(graph_server.id, []).extend(mail_without_server)
                mail_without_server = []
        
        # Process all emails with Graph API
        result = True
        for server_id, mail_ids in mail_by_server.items():
            server = self.env['ir.mail_server'].sudo().browse(server_id)
            if server.use_graph_api:
                mail_batch = self.sudo().browse(mail_ids)
                
                # Process each mail individually to avoid a single failure affecting all
                for mail in mail_batch:
                    try:
                        # Mark as attempted to avoid infinite loops
                        mail.sudo().write({'graph_api_attempted': True})
                        
                        # Check if debug mode is enabled
                        debug_mode = server.debug_mode if hasattr(server, 'debug_mode') else False
                        if debug_mode:
                            _logger.info("Processing mail ID %s with Graph API server ID %s (DEBUG mode)", mail.id, server.id)
                            _logger.info("Mail subject: %s", mail.subject)
                            _logger.info("Recipients: %s", mail.email_to)
                        else:
                            _logger.info("Processing mail ID %s with Graph API server ID %s", mail.id, server.id)
                        
                        # Make sure we have a valid token
                        server.refresh_token_if_needed()
                        
                        # Get recipients
                        email_to = mail.email_to
                        email_cc = mail.email_cc
                        
                        # Handle recipients
                        if not email_to and not mail.recipient_ids:
                            _logger.info("Mail %s has no recipients, setting to EXCEPTION", mail.id)
                            mail.sudo().write({'state': 'exception', 'failure_reason': 'No recipient specified'})
                            if auto_commit:
                                self.env.cr.commit()
                            continue
                        
                        # Prepare the email data
                        from_email = server.ms_sender_email
                        if not from_email:
                            _logger.warning("No sender email configured on server, using company email")
                            from_email = mail.email_from or self.env.company.email
                            # Remove display name part if present
                            if '<' in from_email:
                                from_email = from_email.split('<')[1].split('>')[0]
                        
                        subject = mail.subject or ''
                        
                        # Get body
                        body = mail.body_html or mail.body or '<p></p>'
                        content_type = 'HTML' if mail.body_html else 'Text'
                        
                        if debug_mode:
                            _logger.info("Email details - From: %s, To: %s, Subject: %s, Content type: %s", 
                                        from_email, email_to, subject, content_type)
                        
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
                                    # Remove display name part if present
                                    if '<' in email:
                                        email = email.split('<')[1].split('>')[0]
                                    to_recipients.append({"emailAddress": {"address": email}})
                        
                        for partner in mail.recipient_ids:
                            if partner.email:
                                to_recipients.append({"emailAddress": {"address": partner.email}})
                        
                        cc_recipients = []
                        if email_cc:
                            for email in email_cc.split(','):
                                email = email.strip()
                                if email:
                                    # Remove display name part if present
                                    if '<' in email:
                                        email = email.split('<')[1].split('>')[0]
                                    cc_recipients.append({"emailAddress": {"address": email}})
                        
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
                        
                        # Process attachments with size limits
                        max_attachment_size = 35 * 1024 * 1024  # 35MB is Microsoft's limit
                        total_size = 0
                        skipped_attachments = []
                        
                        if mail.attachment_ids:
                            if debug_mode:
                                _logger.info("Processing %s attachments", len(mail.attachment_ids))
                            
                            attachments = []
                            
                            for attachment in mail.attachment_ids:
                                try:
                                    attachment_size = len(attachment.datas or b'')
                                    
                                    # Skip if this would exceed the limit
                                    if total_size + attachment_size > max_attachment_size:
                                        skipped_attachments.append(attachment.name)
                                        continue
                                        
                                    attachment_data = {
                                        "@odata.type": "#microsoft.graph.fileAttachment",
                                        "name": attachment.name,
                                        "contentType": attachment.mimetype or "application/octet-stream",
                                        "contentBytes": base64.b64encode(attachment.datas).decode('utf-8')
                                    }
                                    attachments.append(attachment_data)
                                    total_size += attachment_size
                                    
                                    if debug_mode:
                                        _logger.info("Added attachment: %s (%s bytes)", 
                                                    attachment.name, len(attachment.datas))
                                except Exception as e:
                                    _logger.error("Failed to add attachment %s: %s", attachment.name, str(e))
                                    skipped_attachments.append(f"{attachment.name} (error)")
                            
                            if attachments:
                                email_payload["message"]["attachments"] = attachments
                            
                            if skipped_attachments:
                                _logger.warning("Skipped attachments due to size limits: %s", 
                                              ', '.join(skipped_attachments))
                        
                        if debug_mode:
                            _logger.info("Sending email via Graph API to %s", graph_url)
                        else:
                            _logger.info("Sending email via Graph API")
                        
                        # Send the request with timeout to prevent freezing
                        try:
                            response = requests.post(
                                graph_url, 
                                headers=headers, 
                                json=email_payload, 
                                timeout=10  # 10 second timeout to prevent freezing
                            )
                            
                            if debug_mode:
                                _logger.info("Email sent response status: %s", response.status_code)
                                if response.status_code not in [200, 202]:
                                    _logger.info("Response content: %s", response.text)
                            else:
                                _logger.info("Email sent response status: %s", response.status_code)
                            
                            if response.status_code not in [200, 202]:
                                error_message = f"Failed to send email: {response.text}"
                                _logger.error(error_message)
                                mail.sudo().write({'state': 'exception', 'failure_reason': error_message})
                            else:
                                _logger.info("Email sent successfully via Microsoft Graph API")
                                mail.sudo().write({'state': 'sent'})
                                
                                # Update message status
                                if mail.mail_message_id:
                                    try:
                                        mail.mail_message_id.sudo().write({'is_mail_sent': True})
                                    except Exception as e:
                                        _logger.warning("Failed to update message sent status: %s", str(e))
                                
                        except Timeout:
                            error_message = "Timeout while sending email via Microsoft Graph API"
                            _logger.error(error_message)
                            mail.sudo().write({'state': 'exception', 'failure_reason': error_message})
                            
                        except RequestException as e:
                            error_message = f"Request error sending email via Microsoft Graph API: {str(e)}"
                            _logger.error(error_message)
                            mail.sudo().write({'state': 'exception', 'failure_reason': error_message})
                            
                        except Exception as e:
                            error_message = f"Error sending email: {str(e)}"
                            _logger.error(error_message)
                            mail.sudo().write({'state': 'exception', 'failure_reason': error_message})
                        
                        # Commit after each email if auto_commit is enabled
                        if auto_commit:
                            self.env.cr.commit()
                            
                    except Exception as e:
                        _logger.error("Error processing mail %s: %s", mail.id, str(e))
                        mail.sudo().write({'state': 'exception', 'failure_reason': str(e)})
                        if auto_commit:
                            self.env.cr.commit()
                        if raise_exception:
                            raise
                
            else:
                # Use standard method for this batch
                _logger.info("Server %s does not use Graph API, using standard method for %s emails", 
                             server_id, len(mail_ids))
                result = result and super(MailMail, self.browse(mail_ids))._send(
                    auto_commit=auto_commit, 
                    raise_exception=raise_exception, 
                    smtp_session=smtp_session,
                    alias_domain_id=alias_domain_id,
                    mail_server=mail_server,
                    post_send_callback=post_send_callback
                )
        
        # Handle remaining emails with standard method
        if mail_without_server:
            _logger.info("Using standard method for %s emails without server", len(mail_without_server))
            result = result and super(MailMail, self.browse(mail_without_server))._send(
                auto_commit=auto_commit, 
                raise_exception=raise_exception, 
                smtp_session=smtp_session,
                alias_domain_id=alias_domain_id,
                mail_server=mail_server,
                post_send_callback=post_send_callback
            )
        
        return result
    
    @api.model
    def process_email_queue(self, ids=None):
        """Inherit to handle Graph API emails with potential timeouts"""
        if ids:
            mail_ids = ids
        else:
            mail_ids = self.search([('state', '=', 'outgoing')]).ids
        
        if mail_ids:
            _logger.info('Processing email queue: %s emails', len(mail_ids))
            
            # Group mail by server to optimize sending
            mail_to_send = {}
            for mail in self.browse(mail_ids):
                if mail.mail_server_id:
                    mail_to_send.setdefault(mail.mail_server_id.id, []).append(mail.id)
                else:
                    mail_to_send.setdefault(None, []).append(mail.id)
            
            # Process each server group separately to prevent one bad server from affecting all emails
            for server_id, server_mail_ids in mail_to_send.items():
                try:
                    # Process in smaller batches to avoid timeouts
                    batch_size = 20  # Reasonable batch size for most scenarios
                    for i in range(0, len(server_mail_ids), batch_size):
                        batch_ids = server_mail_ids[i:i+batch_size]
                        self.sudo().browse(batch_ids).send(auto_commit=True)
                except Exception as e:
                    _logger.error('Failed processing mail queue for server %s: %s', server_id, e)
        
        return True
        
    def mark_outgoing(self):
        """Override to reset the graph_api_attempted flag when marking as outgoing"""
        res = super(MailMail, self).mark_outgoing()
        # Reset the graph_api_attempted flag
        self.sudo().write({'graph_api_attempted': False})
        return res 