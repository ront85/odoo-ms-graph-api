import logging
import traceback
import sys
import time
import threading
from odoo import api, models

_logger = logging.getLogger(__name__)

class MailMailFixBCC(models.Model):
    _inherit = 'mail.mail'
    
    def _send_graph_api_fixed(self, auto_commit=False, raise_exception=False, smtp_session=None, 
                              mail_server=None, post_send_callback=None):
        """Improved implementation of Graph API email sending with better error handling"""
        import json
        import base64
        import requests
        from requests.exceptions import Timeout, RequestException
        
        mail_ids = self.ids
        _logger.info(f"=== MAIL_FIX: _send_graph_api_fixed called for mail IDs {mail_ids} ===")
        
        if not self.ids:
            return True
            
        # Process each mail individually to avoid a single mail causing problems
        for mail in self.browse(self.ids):
            mail_start_time = time.time()
            _logger.info(f"=== MAIL_FIX: Processing mail ID {mail.id} with Graph API ===")
            
            # Set timeout for the watchdog
            timeout_detected = {'value': False}
            
            def mail_watchdog():
                time.sleep(10)  # Shorter timeout per individual email
                if not timeout_detected['value']:
                    _logger.error(f"=== MAIL_FIX: Individual mail {mail.id} taking too long, aborting ===")
                    # Cannot directly modify the mail state from this thread, just log it
            
            mail_timer = threading.Thread(target=mail_watchdog)
            mail_timer.daemon = True
            mail_timer.start()
            
            try:
                # Already marked this mail as attempted with Graph API
                if mail.graph_api_attempted:
                    _logger.info(f"=== MAIL_FIX: Mail ID {mail.id} already attempted with Graph API, skipping ===")
                    # Skip this mail, it will be processed by standard method
                    continue
                
                # Mark as attempted to prevent future retries with Graph API
                mail.graph_api_attempted = True
                
                # Check if debug mode is enabled
                debug_mode = mail_server.debug_mode if hasattr(mail_server, 'debug_mode') else False
                
                # Make sure we have a valid token with shorter timeout
                try:
                    _logger.info(f"=== MAIL_FIX: Refreshing token if needed for mail {mail.id} ===")
                    mail_server.refresh_token_if_needed()
                except Exception as token_error:
                    _logger.error(f"=== MAIL_FIX: Token refresh failed: {str(token_error)} ===")
                    mail.write({'state': 'exception', 'failure_reason': f"Token refresh failed: {str(token_error)}"})
                    if auto_commit:
                        self.env.cr.commit()
                    continue
                
                # Get recipients
                email_to = mail.email_to
                email_cc = mail.email_cc
                # BCC is not directly available in mail.mail, skip it
                
                if not email_to and not mail.recipient_ids:
                    _logger.info(f"=== MAIL_FIX: Mail {mail.id} has no recipients, setting to EXCEPTION ===")
                    mail.write({'state': 'exception', 'failure_reason': 'No recipient specified'})
                    if auto_commit:
                        self.env.cr.commit()
                    continue
                
                # Extract mail content with error handling
                try:
                    subject = mail.subject or "(No Subject)"
                    body = mail.body_html or "<p>No message content</p>"
                    content_type = "HTML"
                except Exception as content_error:
                    _logger.error(f"=== MAIL_FIX: Error extracting content: {str(content_error)} ===")
                    mail.write({'state': 'exception', 'failure_reason': f"Content extraction error: {str(content_error)}"})
                    if auto_commit:
                        self.env.cr.commit()
                    continue
                
                # Prepare the email data
                from_email = mail_server.ms_sender_email
                if not from_email:
                    _logger.warning("=== MAIL_FIX: No sender email configured on server, using company email ===")
                    from_email = mail.email_from or self.env.company.email
                
                # Prepare Graph API request
                try:
                    graph_url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"
                    headers = {
                        'Authorization': f'Bearer {mail_server.ms_access_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    # Prepare recipients with better error handling
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
                    
                    # Create basic email payload
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
                    
                    # Process attachments with size limits and better error handling
                    max_total_size = 35 * 1024 * 1024  # 35MB limit for total attachments (Microsoft restriction)
                    current_total_size = 0
                    skipped_attachments = []
                    
                    if mail.attachment_ids:
                        _logger.info(f"=== MAIL_FIX: Processing {len(mail.attachment_ids)} attachments for mail {mail.id} ===")
                        attachments = []
                        
                        for attachment in mail.attachment_ids:
                            try:
                                attachment_size = len(attachment.datas or b'')
                                
                                # Skip if this attachment would exceed the limit
                                if current_total_size + attachment_size > max_total_size:
                                    skipped_attachments.append(attachment.name)
                                    continue
                                
                                _logger.info(f"=== MAIL_FIX: Adding attachment {attachment.name} ({attachment_size} bytes) ===")
                                attachment_data = {
                                    "@odata.type": "#microsoft.graph.fileAttachment",
                                    "name": attachment.name,
                                    "contentType": attachment.mimetype or "application/octet-stream",
                                    "contentBytes": base64.b64encode(attachment.datas).decode('utf-8')
                                }
                                attachments.append(attachment_data)
                                current_total_size += attachment_size
                                
                            except Exception as e:
                                _logger.error(f"=== MAIL_FIX: Failed to add attachment {attachment.name}: {str(e)} ===")
                                skipped_attachments.append(f"{attachment.name} (error)")
                        
                        if attachments:
                            email_payload["message"]["attachments"] = attachments
                    
                    if skipped_attachments:
                        _logger.warning(f"=== MAIL_FIX: Skipped attachments due to size limits: {', '.join(skipped_attachments)} ===")
                
                    # Send the request to Graph API with strict timeout
                    _logger.info(f"=== MAIL_FIX: Sending API request for mail {mail.id} ===")
                    
                    # Use a smaller timeout to prevent freezing the system
                    response = requests.post(
                        graph_url, 
                        headers=headers, 
                        json=email_payload, 
                        timeout=10  # Reduced timeout
                    )
                    
                    _logger.info(f"=== MAIL_FIX: Received API response for mail {mail.id}: status {response.status_code} ===")
                    
                    # Handle response
                    if response.status_code not in [200, 202]:
                        error_message = f"Failed to send email: {response.text}"
                        _logger.error(error_message)
                        mail.write({'state': 'exception', 'failure_reason': error_message})
                    else:
                        _logger.info(f"=== MAIL_FIX: Email {mail.id} sent successfully ===")
                        mail.write({'state': 'sent'})
                        
                except Timeout:
                    error_message = f"Timeout while sending email via Microsoft Graph API (mail ID: {mail.id})"
                    _logger.error(error_message)
                    mail.write({'state': 'exception', 'failure_reason': error_message})
                    
                except RequestException as e:
                    error_message = f"Request exception while sending email via Microsoft Graph API: {str(e)}"
                    _logger.error(error_message)
                    mail.write({'state': 'exception', 'failure_reason': error_message})
                    
                except Exception as e:
                    error_message = f"Error sending email: {str(e)}"
                    _logger.error(error_message)
                    _logger.error(traceback.format_exc())
                    mail.write({'state': 'exception', 'failure_reason': error_message})
                
                if auto_commit:
                    _logger.info(f"=== MAIL_FIX: Committing after mail {mail.id} ===")
                    self.env.cr.commit()
                
                # Log processing time
                mail_end_time = time.time()
                mail_processing_time = mail_end_time - mail_start_time
                _logger.info(f"=== MAIL_FIX: Mail {mail.id} processed in {mail_processing_time:.2f} seconds ===")
                
            except Exception as mail_error:
                _logger.error(f"=== MAIL_FIX: Error processing mail {mail.id}: {str(mail_error)} ===")
                _logger.error(traceback.format_exc())
                mail.write({'state': 'exception', 'failure_reason': str(mail_error)})
                if auto_commit:
                    self.env.cr.commit()
                if raise_exception:
                    raise
            
            finally:
                # Mark as completed
                timeout_detected['value'] = True
        
        return True


class IrMailServerSendEmailFixed(models.Model):
    _inherit = 'ir.mail_server'
    
    def _send_email_graph_api(self, message, mail_server):
        """Send email using Microsoft Graph API"""
        import base64
        import json
        import requests
        from email.policy import default
        
        _logger.info(f"=== MAIL_FIX: Sending email via Graph API ===")
        
        # Add a timeout to prevent hanging
        timeout_detected = {'value': False}
        
        def timeout_watchdog():
            time.sleep(10)  # 10 seconds should be enough for a single email
            if not timeout_detected['value']:
                _logger.error(f"=== MAIL_FIX: Timeout in Graph API sending ===")
        
        timer = threading.Thread(target=timeout_watchdog)
        timer.daemon = True
        timer.start()
        
        try:
            # Refresh token if needed
            mail_server.refresh_token_if_needed()
            
            # Get sender
            from_email = mail_server.ms_sender_email
            if not from_email:
                from_email = message.get('From')
                if '<' in from_email:
                    from_email = from_email.split('<')[1].split('>')[0]
            
            # Setup Graph API request
            graph_url = f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail"
            headers = {
                'Authorization': f'Bearer {mail_server.ms_access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get recipients
            to_recipients = []
            if message.get('To'):
                for email in message.get('To').split(','):
                    email = email.strip()
                    if email:
                        if '<' in email:
                            email = email.split('<')[1].split('>')[0]
                        to_recipients.append({"emailAddress": {"address": email}})
            
            cc_recipients = []
            if message.get('Cc'):
                for email in message.get('Cc').split(','):
                    email = email.strip()
                    if email:
                        if '<' in email:
                            email = email.split('<')[1].split('>')[0]
                        cc_recipients.append({"emailAddress": {"address": email}})
            
            bcc_recipients = []
            if message.get('Bcc'):
                for email in message.get('Bcc').split(','):
                    email = email.strip()
                    if email:
                        if '<' in email:
                            email = email.split('<')[1].split('>')[0]
                        bcc_recipients.append({"emailAddress": {"address": email}})
            
            # Extract subject
            subject = message.get('Subject', '(No Subject)')
            
            # Extract message body
            if message.is_multipart():
                for part in message.get_payload():
                    if part.get_content_type() == 'text/html':
                        body = part.get_payload(decode=True).decode()
                        content_type = "HTML"
                        break
                    elif part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode()
                        content_type = "Text"
                else:
                    # If no text parts found, use first part's payload or empty
                    body = message.get_payload(0).get_payload(decode=True).decode() if message.get_payload() else ""
                    content_type = "Text"
            else:
                body = message.get_payload(decode=True).decode() if message.get_payload() else ""
                content_type = "Text"
            
            # Create the base message
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
            
            # Process attachments
            if message.is_multipart():
                attachments = []
                for part in message.get_payload():
                    if part.get_content_disposition() == 'attachment':
                        try:
                            attachment_data = {
                                "@odata.type": "#microsoft.graph.fileAttachment",
                                "name": part.get_filename() or 'attachment',
                                "contentType": part.get_content_type() or "application/octet-stream",
                                "contentBytes": base64.b64encode(part.get_payload(decode=True)).decode('utf-8')
                            }
                            attachments.append(attachment_data)
                        except Exception as e:
                            _logger.error(f"=== MAIL_FIX: Error adding attachment: {str(e)} ===")
                
                if attachments:
                    email_payload["message"]["attachments"] = attachments
            
            # Send the request with timeout
            response = requests.post(
                graph_url, 
                headers=headers, 
                json=email_payload, 
                timeout=10  # 10 second timeout
            )
            
            # Check response
            if response.status_code not in [200, 202]:
                error_message = f"Graph API error: {response.text}"
                _logger.error(f"=== MAIL_FIX: {error_message} ===")
                raise Exception(error_message)
            
            # Get message ID from response if available
            message_id = None
            try:
                message_id = response.headers.get('x-ms-request-id') or message.get('Message-ID')
            except:
                message_id = message.get('Message-ID', 'unknown')
            
            _logger.info(f"=== MAIL_FIX: Email sent successfully via Graph API: {message_id} ===")
            
            # Return message ID
            return message_id
            
        except Exception as e:
            _logger.error(f"=== MAIL_FIX: Error in Graph API sending: {str(e)} ===")
            _logger.error(traceback.format_exc())
            raise
            
        finally:
            # Mark timeout as done
            timeout_detected['value'] = True 