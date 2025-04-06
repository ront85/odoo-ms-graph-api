import logging
import time
import traceback
import threading
from odoo import api, models

_logger = logging.getLogger(__name__)

class IrMailServerFix(models.Model):
    _inherit = 'ir.mail_server'
    
    def connect(self, host=None, port=None, user=None, password=None, encryption=None,
               smtp_from=None, ssl_certificate=None, ssl_private_key=None, smtp_debug=False, mail_server_id=None,
               allow_archived=False):
        """Override to prevent freezing with Graph API mail servers."""
        
        # If mail_server_id is provided, check if it's a Graph API server
        if mail_server_id:
            mail_server = self.browse(mail_server_id)
            use_graph_api = mail_server.use_graph_api if hasattr(mail_server, 'use_graph_api') else False
            
            if use_graph_api:
                _logger.info(f"=== MAIL_FIX: Using special connect handling for Graph API server {mail_server.name} ===")
                # For Graph API servers, we don't need a real SMTP connection
                # Instead, return a dummy connection object that works with the rest of the code
                from types import SimpleNamespace
                
                # Create a dummy connection that mimics an SMTP connection
                # but doesn't actually connect to anything
                dummy_connection = SimpleNamespace()
                dummy_connection.quit = lambda: None
                dummy_connection.close = lambda: None
                dummy_connection.helo = lambda: (200, b'OK')
                dummy_connection.has_extn = lambda x: False
                dummy_connection.ehlo_or_helo_if_needed = lambda: None
                
                _logger.info(f"=== MAIL_FIX: Returning dummy SMTP connection for Graph API server ===")
                return dummy_connection
        
        # Add watchdog for SMTP connections
        thread_id = threading.get_ident()
        _logger.info(f"=== MAIL_FIX: connect method called (Thread: {thread_id}) ===")
        
        # Add watchdog to detect freezes
        freeze_detected = {'value': False}
        
        def watchdog_timer():
            _logger.info(f"=== MAIL_FIX: Watchdog timer started for connect (Thread: {thread_id}) ===")
            time.sleep(15)  # 15 second timeout for SMTP connection
            if not freeze_detected['value']:
                freeze_message = f"=== MAIL_FIX: FREEZE DETECTED! SMTP connect is taking too long ===\n"
                freeze_message += f"Stack trace:\n{''.join(traceback.format_stack())}"
                _logger.error(freeze_message)
                
                # Force terminate this connect operation after 25 seconds total
                time.sleep(10)
                if not freeze_detected['value']:
                    _logger.error(f"=== MAIL_FIX: CRITICAL FREEZE in SMTP connect! ===")
                    
                    # Unfortunately, we can't really cancel the SMTP connection attempt from here
                    # But we can log it to help identify the issue
        
        # Only start the watchdog if we're not testing
        if host and port and not self.env.registry.in_test_mode():
            timer = threading.Thread(target=watchdog_timer)
            timer.daemon = True
            timer.start()
        
        try:
            # Call the original method
            result = super(IrMailServerFix, self).connect(
                host=host, port=port, user=user, password=password, 
                encryption=encryption, smtp_from=smtp_from, 
                ssl_certificate=ssl_certificate, ssl_private_key=ssl_private_key, 
                smtp_debug=smtp_debug, mail_server_id=mail_server_id,
                allow_archived=allow_archived
            )
            
            # Mark as completed before returning
            freeze_detected['value'] = True
            
            return result
        except Exception as e:
            _logger.error(f"=== MAIL_FIX: Exception in connect method: {str(e)} ===")
            _logger.error(traceback.format_exc())
            
            # Mark as completed before re-raising
            freeze_detected['value'] = True
            
            raise
        finally:
            # Mark as completed in finally block to ensure it happens
            freeze_detected['value'] = True


class IrMailServerSendEmail(models.Model):
    _inherit = 'ir.mail_server'
    
    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_debug=False, smtp_session=None):
        """Override to handle Graph API mail servers correctly"""
        
        # Check if mail_server_id is provided and it's a Graph API server
        use_graph_api = False
        if mail_server_id:
            mail_server = self.browse(mail_server_id)
            use_graph_api = mail_server.use_graph_api if hasattr(mail_server, 'use_graph_api') else False
        
        if use_graph_api:
            _logger.info(f"=== MAIL_FIX: Using Graph API to send email with server ID {mail_server_id} ===")
            try:
                # Implementation for Graph API sending
                return self._send_email_graph_api(message, mail_server)
            except Exception as e:
                _logger.error(f"=== MAIL_FIX: Error using Graph API: {str(e)} ===")
                _logger.error(traceback.format_exc())
                # Fall back to standard method
        
        # Call original method for non-Graph API emails
        return super(IrMailServerSendEmail, self).send_email(
            message, mail_server_id=mail_server_id, 
            smtp_server=smtp_server, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_password, 
            smtp_encryption=smtp_encryption,
            smtp_debug=smtp_debug, smtp_session=smtp_session
        )
    
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