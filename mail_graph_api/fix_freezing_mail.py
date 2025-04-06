import logging
import traceback
import sys
import time
import threading
from odoo import api, models
from odoo.tools.misc import formataddr

_logger = logging.getLogger(__name__)

class MailMailFix(models.Model):
    _inherit = 'mail.mail'
    
    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        """Override to fix freezing in Graph API mail sending"""
        thread_id = threading.get_ident()
        mail_ids = self.ids
        _logger.info(f"=== MAIL_FIX: _send method called for mail IDs {mail_ids} (Thread: {thread_id}) ===")
        
        # Add watchdog to detect freezes
        freeze_detected = {'value': False}
        
        def watchdog_timer():
            _logger.info(f"=== MAIL_FIX: Watchdog timer started for _send {mail_ids} (Thread: {thread_id}) ===")
            time.sleep(30)  # Wait 30 seconds
            if not freeze_detected['value']:
                current_stack = ''.join(traceback.format_stack())
                all_threads_stack = {}
                
                # Get stack traces for all threads
                for th_id, frame in sys._current_frames().items():
                    all_threads_stack[th_id] = ''.join(traceback.format_stack(frame))
                
                freeze_message = f"=== MAIL_FIX: FREEZE DETECTED! _send for {mail_ids} is taking too long ===\n"
                freeze_message += f"Current thread stack trace:\n{current_stack}\n"
                freeze_message += "=== All thread stack traces ===\n"
                
                for th_id, stack in all_threads_stack.items():
                    freeze_message += f"\n--- Thread {th_id} ---\n{stack}\n"
                
                _logger.error(freeze_message)
                
                # Force terminate this mail send operation after 45 seconds
                time.sleep(15)
                if not freeze_detected['value']:
                    _logger.error(f"=== MAIL_FIX: CRITICAL FREEZE! Killing mail operation for {mail_ids} ===")
                    
                    # Mark any outgoing emails in this batch as failed
                    try:
                        mails = self.browse(mail_ids)
                        for mail in mails:
                            if mail.state == 'outgoing':
                                mail.write({
                                    'state': 'exception',
                                    'failure_reason': 'Mail operation timed out (system frozen)',
                                    'graph_api_attempted': True
                                })
                        _logger.error(f"=== MAIL_FIX: Marked frozen emails as failed: {mail_ids} ===")
                    except Exception as e:
                        _logger.error(f"=== MAIL_FIX: Failed to mark emails as failed: {str(e)} ===")
        
        # Start watchdog timer
        timer = threading.Thread(target=watchdog_timer)
        timer.daemon = True
        timer.start()
        
        try:
            # Check if this is a Graph API mail server
            use_graph_api = False
            if mail_server and hasattr(mail_server, 'use_graph_api'):
                use_graph_api = mail_server.use_graph_api
            
            if use_graph_api:
                _logger.info(f"=== MAIL_FIX: Using improved Graph API handling for mail IDs {mail_ids} ===")
                result = self._send_graph_api_fixed(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                    mail_server=mail_server,
                    post_send_callback=post_send_callback
                )
            else:
                _logger.info(f"=== MAIL_FIX: Using standard send method for mail IDs {mail_ids} ===")
                # Call the original method for non-Graph API emails
                result = super(MailMailFix, self)._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session,
                    alias_domain_id=alias_domain_id,
                    mail_server=mail_server,
                    post_send_callback=post_send_callback
                )
            
            _logger.info(f"=== MAIL_FIX: _send method completed for mail IDs {mail_ids} (Thread: {thread_id}) ===")
            
            # Mark as completed before returning
            freeze_detected['value'] = True
            
            return result
        except Exception as e:
            _logger.error(f"=== MAIL_FIX: Exception in _send method for {mail_ids}: {str(e)} ===")
            _logger.error(traceback.format_exc())
            
            # Mark as completed before re-raising
            freeze_detected['value'] = True
            
            raise
        finally:
            # Mark as completed in finally block to ensure it happens
            freeze_detected['value'] = True
    
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
                email_bcc = mail.email_bcc
                
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
                    
                    bcc_recipients = []
                    if email_bcc:
                        for email in email_bcc.split(','):
                            email = email.strip()
                            if email:
                                bcc_recipients.append({"emailAddress": {"address": email}})
                    
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
                    
                    # Add BCC recipients if any
                    if bcc_recipients:
                        email_payload["message"]["bccRecipients"] = bcc_recipients
                    
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