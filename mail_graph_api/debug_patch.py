import sys
import time
import threading
import traceback
import logging
from odoo import api, models
from odoo.tools.misc import formataddr

_logger = logging.getLogger(__name__)

class MailMailDebug(models.Model):
    _inherit = 'mail.mail'
    
    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        """Override to add debugging for mail send process"""
        thread_id = threading.get_ident()
        mail_ids = self.ids
        _logger.info(f"=== MAIL_DEBUG: send method called for mail IDs {mail_ids} (Thread: {thread_id}) ===")
        
        # Add watchdog to detect freezes
        freeze_detected = {'value': False}
        
        def watchdog_timer():
            _logger.info(f"=== MAIL_DEBUG: Watchdog timer started for send {mail_ids} (Thread: {thread_id}) ===")
            time.sleep(30)  # Wait 30 seconds
            if not freeze_detected['value']:
                current_stack = ''.join(traceback.format_stack())
                all_threads_stack = {}
                
                # Get stack traces for all threads
                for th_id, frame in sys._current_frames().items():
                    all_threads_stack[th_id] = ''.join(traceback.format_stack(frame))
                
                freeze_message = f"=== MAIL_DEBUG: FREEZE DETECTED! send for {mail_ids} is taking too long ===\n"
                freeze_message += f"Current thread stack trace:\n{current_stack}\n"
                freeze_message += "=== All thread stack traces ===\n"
                
                for th_id, stack in all_threads_stack.items():
                    freeze_message += f"\n--- Thread {th_id} ---\n{stack}\n"
                
                _logger.error(freeze_message)
                
                # Wait 30 more seconds and check again
                time.sleep(30)
                if not freeze_detected['value']:
                    _logger.error(f"=== MAIL_DEBUG: SEVERE FREEZE! send for {mail_ids} is still stuck after 60 seconds ===")
        
        # Start watchdog timer
        timer = threading.Thread(target=watchdog_timer)
        timer.daemon = True
        timer.start()
        
        try:
            result = super(MailMailDebug, self).send(
                auto_commit=auto_commit, 
                raise_exception=raise_exception,
                post_send_callback=post_send_callback
            )
            
            _logger.info(f"=== MAIL_DEBUG: send method completed for mail IDs {mail_ids} (Thread: {thread_id}) ===")
            
            # Mark as completed before returning
            freeze_detected['value'] = True
            
            return result
        except Exception as e:
            _logger.error(f"=== MAIL_DEBUG: Exception in send method for {mail_ids}: {str(e)} ===")
            _logger.error(traceback.format_exc())
            
            # Mark as completed before re-raising
            freeze_detected['value'] = True
            
            raise
        finally:
            # Mark as completed in finally block to ensure it happens
            freeze_detected['value'] = True

class MailMailSendDebug(models.Model):
    _inherit = 'mail.mail'
    
    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, alias_domain_id=False,
              mail_server=False, post_send_callback=None):
        """Override to add debugging for mail _send process"""
        thread_id = threading.get_ident()
        mail_ids = self.ids
        _logger.info(f"=== MAIL_DEBUG: _send method called for mail IDs {mail_ids} (Thread: {thread_id}) ===")
        
        # Add watchdog to detect freezes
        freeze_detected = {'value': False}
        
        def watchdog_timer():
            _logger.info(f"=== MAIL_DEBUG: Watchdog timer started for _send {mail_ids} (Thread: {thread_id}) ===")
            time.sleep(30)  # Wait 30 seconds
            if not freeze_detected['value']:
                current_stack = ''.join(traceback.format_stack())
                freeze_message = f"=== MAIL_DEBUG: FREEZE DETECTED! _send for {mail_ids} is taking too long ===\n"
                freeze_message += f"Stack trace:\n{current_stack}"
                _logger.error(freeze_message)
        
        # Start watchdog timer
        timer = threading.Thread(target=watchdog_timer)
        timer.daemon = True
        timer.start()
        
        try:
            result = super(MailMailSendDebug, self)._send(
                auto_commit=auto_commit,
                raise_exception=raise_exception,
                smtp_session=smtp_session,
                alias_domain_id=alias_domain_id,
                mail_server=mail_server,
                post_send_callback=post_send_callback
            )
            
            _logger.info(f"=== MAIL_DEBUG: _send method completed for mail IDs {mail_ids} (Thread: {thread_id}) ===")
            
            # Mark as completed before returning
            freeze_detected['value'] = True
            
            return result
        except Exception as e:
            _logger.error(f"=== MAIL_DEBUG: Exception in _send method for {mail_ids}: {str(e)} ===")
            _logger.error(traceback.format_exc())
            
            # Mark as completed before re-raising
            freeze_detected['value'] = True
            
            raise
        finally:
            # Mark as completed in finally block to ensure it happens
            freeze_detected['value'] = True


class IrMailServerDebug(models.Model):
    _inherit = 'ir.mail_server'
    
    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_debug=False, smtp_session=None):
        """Override to add detailed diagnostics for send_email"""
        thread_id = threading.get_ident()
        msg_id = message.get('Message-Id', 'unknown_id')
        _logger.info(f"=== MAIL_DEBUG: send_email started for message {msg_id} (Thread: {thread_id}) ===")
        
        # Create a watchdog timer to detect freezes
        freeze_detected = {'value': False}
        
        def watchdog_timer():
            _logger.info(f"=== MAIL_DEBUG: Watchdog timer started for send_email {msg_id} (Thread: {thread_id}) ===")
            time.sleep(30)  # Wait 30 seconds
            if not freeze_detected['value']:
                all_threads_stack = {}
                
                # Get stack traces for all threads
                for th_id, frame in sys._current_frames().items():
                    all_threads_stack[th_id] = ''.join(traceback.format_stack(frame))
                
                freeze_message = f"=== MAIL_DEBUG: FREEZE DETECTED! send_email for {msg_id} is taking too long ===\n"
                freeze_message += "=== All thread stack traces ===\n"
                
                for th_id, stack in all_threads_stack.items():
                    freeze_message += f"\n--- Thread {th_id} ---\n{stack}\n"
                    
                _logger.error(freeze_message)
            
        # Start watchdog timer
        timer = threading.Thread(target=watchdog_timer)
        timer.daemon = True
        timer.start()
        
        try:
            # Check if mail_server_id uses Graph API
            use_graph_api = False
            if mail_server_id:
                mail_server = self.browse(mail_server_id)
                use_graph_api = mail_server.use_graph_api if hasattr(mail_server, 'use_graph_api') else False
                _logger.info(f"=== MAIL_DEBUG: Using mail server ID {mail_server_id}, use_graph_api={use_graph_api} ===")
            
            # Log key parts of the email
            email_to = message.get('To', 'unknown')
            email_from = message.get('From', 'unknown')
            subject = message.get('Subject', 'unknown')
            attachments = bool(message.get_payload()) if hasattr(message, 'get_payload') else 'unknown'
            
            _logger.info(f"=== MAIL_DEBUG: Email details - From: {email_from}, To: {email_to}, Subject: {subject}, Has attachments: {attachments} ===")
            
            # Call the original method
            result = super(IrMailServerDebug, self).send_email(
                message, mail_server_id=mail_server_id, smtp_server=smtp_server, 
                smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password, 
                smtp_encryption=smtp_encryption, smtp_debug=smtp_debug, 
                smtp_session=smtp_session
            )
            
            _logger.info(f"=== MAIL_DEBUG: send_email completed for message {msg_id} (Thread: {thread_id}) ===")
            
            # Mark as completed before returning
            freeze_detected['value'] = True
            
            return result
        except Exception as e:
            _logger.error(f"=== MAIL_DEBUG: Exception in send_email for {msg_id}: {str(e)} ===")
            _logger.error(traceback.format_exc())
            
            # Mark as completed before re-raising
            freeze_detected['value'] = True
            
            raise
        finally:
            # Mark as completed in finally block to ensure it happens
            freeze_detected['value'] = True 