import logging
import json
import datetime
import requests
from requests.exceptions import Timeout, RequestException
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'
    
    use_graph_api = fields.Boolean(string='Use Microsoft Graph API', default=False,
                                   help='If checked, this mail server will use Microsoft Graph API to send emails')
    ms_client_id = fields.Char(string='Microsoft App Client ID')
    ms_client_secret = fields.Char(string='Microsoft App Client Secret')
    ms_tenant_id = fields.Char(string='Microsoft Tenant ID')
    ms_sender_email = fields.Char(string='Microsoft Sender Email', 
                                 help='The email address that will be used to send emails via Microsoft Graph API')
    ms_access_token = fields.Char(string='Microsoft Access Token', copy=False)
    ms_refresh_token = fields.Char(string='Microsoft Refresh Token', copy=False)
    ms_token_expiry = fields.Datetime(string='Token Expiry Date', copy=False)
    
    # Fix compute method for smtp_authentication_info
    smtp_authentication_info = fields.Char(compute='_compute_smtp_authentication_info')
    
    @api.depends('smtp_authentication', 'use_graph_api')
    def _compute_smtp_authentication_info(self):
        for server in self:
            if server.use_graph_api:
                server.smtp_authentication_info = _("Authentication managed by Microsoft Graph API")
            else:
                # Let the original compute method handle it
                if hasattr(super(IrMailServer, server), '_compute_smtp_authentication_info'):
                    # Call the super method if it exists
                    super(IrMailServer, server)._compute_smtp_authentication_info()
                else:
                    # Default value if super method doesn't exist
                    auth_type = server.smtp_authentication
                    server.smtp_authentication_info = auth_type
    
    @api.onchange('use_graph_api')
    def _onchange_use_graph_api(self):
        if self.use_graph_api:
            # When Graph API is enabled, SMTP is not needed
            self.smtp_host = False
            self.smtp_port = False
            self.smtp_user = False
            self.smtp_pass = False
            self.smtp_encryption = False
            self.smtp_debug = False
            
    def refresh_token_if_needed(self):
        """Refresh the Microsoft Graph API token if it has expired or is about to expire"""
        self.ensure_one()
        
        if not self.use_graph_api:
            return
            
        if not self.ms_refresh_token:
            raise UserError(_("Microsoft Refresh Token not found. Please authenticate with Microsoft Graph API."))
            
        # Check if token is expired or will expire in the next 5 minutes
        now = datetime.datetime.now()
        if not self.ms_token_expiry or self.ms_token_expiry <= fields.Datetime.now() + datetime.timedelta(minutes=5):
            _logger.info("Token expired or about to expire, refreshing...")
            try:
                # Refresh the token
                token_url = f'https://login.microsoftonline.com/{self.ms_tenant_id}/oauth2/v2.0/token'
                token_data = {
                    'client_id': self.ms_client_id,
                    'client_secret': self.ms_client_secret,
                    'scope': 'https://graph.microsoft.com/.default',
                    'grant_type': 'refresh_token',
                    'refresh_token': self.ms_refresh_token
                }
                
                response = requests.post(token_url, data=token_data, timeout=10)
                
                if response.status_code != 200:
                    _logger.error(f"Failed to refresh token: {response.text}")
                    raise UserError(_("Failed to refresh Microsoft Graph API token: %s") % response.text)
                    
                token_info = response.json()
                
                # Update the tokens
                values = {
                    'ms_access_token': token_info.get('access_token'),
                }
                
                # Only update refresh token if a new one was provided
                if token_info.get('refresh_token'):
                    values['ms_refresh_token'] = token_info.get('refresh_token')
                    
                # Calculate and store expiry time
                expires_in = token_info.get('expires_in', 3600)  # Default to 1 hour if not specified
                values['ms_token_expiry'] = fields.Datetime.now() + datetime.timedelta(seconds=expires_in)
                
                # Use sudo to avoid permission issues
                self.sudo().write(values)
                
                _logger.info("Microsoft Graph API token refreshed successfully")
                
            except Timeout:
                _logger.error("Timeout refreshing Microsoft Graph API token")
                raise UserError(_("Timeout refreshing Microsoft Graph API token. Please try again."))
            except Exception as e:
                _logger.error(f"Error refreshing Microsoft Graph API token: {str(e)}")
                raise UserError(_("Error refreshing Microsoft Graph API token: %s") % str(e))
                
        return True
    
    def connect(self, host=None, port=None, user=None, password=None, encryption=None,
               smtp_from=None, ssl_certificate=None, ssl_private_key=None, smtp_debug=False, mail_server_id=None):
        """Override to handle Graph API mail servers"""
        # If mail_server_id is provided, check if it's a Graph API server
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
            if hasattr(mail_server, 'use_graph_api') and mail_server.use_graph_api:
                _logger.info("Using Graph API instead of SMTP connection for server %s", mail_server.name)
                # For Graph API servers, return a dummy connection
                # that mimics an SMTP connection but doesn't actually connect
                from types import SimpleNamespace
                dummy_connection = SimpleNamespace()
                dummy_connection.quit = lambda: None
                dummy_connection.close = lambda: None
                dummy_connection.helo = lambda: (200, b'OK')
                dummy_connection.has_extn = lambda x: False
                dummy_connection.ehlo_or_helo_if_needed = lambda: None
                dummy_connection.sendmail = lambda *args, **kwargs: {}
                dummy_connection.send_message = lambda *args, **kwargs: {}
                return dummy_connection
        
        # For regular mail servers, call the original method
        return super(IrMailServer, self).connect(
            host=host, port=port, user=user, password=password, 
            encryption=encryption, smtp_from=smtp_from, 
            ssl_certificate=ssl_certificate, ssl_private_key=ssl_private_key, 
            smtp_debug=smtp_debug
        )
    
    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_debug=False, smtp_session=None):
        """Override to support Microsoft Graph API for sending emails"""
        # Check if we should use Graph API
        use_graph_api = False
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
            use_graph_api = mail_server.use_graph_api if hasattr(mail_server, 'use_graph_api') else False
        
        if use_graph_api:
            _logger.info("Sending email via Microsoft Graph API")
            return self._send_email_graph_api(message, mail_server)
        
        # If not using Graph API, use the standard method
        return super(IrMailServer, self).send_email(
            message, mail_server_id=mail_server_id, 
            smtp_server=smtp_server, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_password, 
            smtp_encryption=smtp_encryption,
            smtp_debug=smtp_debug, smtp_session=smtp_session
        )
    
    def _send_email_graph_api(self, message, mail_server):
        """Send email using Microsoft Graph API"""
        import base64
        
        _logger.info("Preparing email for Microsoft Graph API")
        
        try:
            # Refresh token if needed
            mail_server.sudo().refresh_token_if_needed()
            
            # Get sender email
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
            
            # Extract recipients
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
            body = ""
            content_type = "Text"
            
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
                    # If no text parts found, use first part or empty
                    if message.get_payload():
                        body = message.get_payload(0).get_payload(decode=True).decode() if message.get_payload() else ""
                        content_type = "Text"
            else:
                body = message.get_payload(decode=True).decode() if message.get_payload() else ""
                content_type = "Text"
            
            # Create the email payload
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
                            
                            # Log diagnostic information for debugging
                            if part.get_content_type() == 'application/pdf':
                                _logger.info("Processing PDF attachment: %s", part.get_filename())
                            
                            attachments.append(attachment_data)
                        except Exception as e:
                            _logger.error(f"Error adding attachment: {str(e)}")
                
                if attachments:
                    email_payload["message"]["attachments"] = attachments
            
            # Send the request with timeout
            _logger.info("Sending email via Graph API to %s", graph_url)
            response = requests.post(
                graph_url, 
                headers=headers, 
                json=email_payload, 
                timeout=10  # 10 second timeout to prevent hanging
            )
            
            # Check response
            if response.status_code not in [200, 202]:
                error_message = f"Graph API error: {response.text}"
                _logger.error(error_message)
                raise UserError(_(error_message))
            
            # Get message ID from response if available
            message_id = None
            try:
                message_id = response.headers.get('x-ms-request-id') or message.get('Message-ID')
            except:
                message_id = message.get('Message-ID', 'unknown')
            
            _logger.info("Email sent successfully via Graph API: %s", message_id)
            
            # Return message ID
            return message_id
            
        except Timeout:
            error_message = "Timeout when sending email via Microsoft Graph API"
            _logger.error(error_message)
            raise UserError(_(error_message))
            
        except RequestException as e:
            error_message = f"Request error when sending email via Microsoft Graph API: {str(e)}"
            _logger.error(error_message)
            raise UserError(_(error_message))
            
        except Exception as e:
            error_message = f"Error sending email via Microsoft Graph API: {str(e)}"
            _logger.error(error_message)
            raise UserError(_(error_message))
    
    @api.model
    def auth_oauth_microsoft(self, authorization_code, redirect_uri):
        """Exchange authorization code for access and refresh tokens"""
        
        # Find a mail server that uses Microsoft Graph API
        mail_server = self.sudo().search([('use_graph_api', '=', True)], limit=1)
        
        if not mail_server:
            raise UserError(_("No mail server configured to use Microsoft Graph API"))
            
        if not mail_server.ms_client_id or not mail_server.ms_client_secret or not mail_server.ms_tenant_id:
            raise UserError(_("Microsoft Graph API credentials not properly configured"))
            
        try:
            # Exchange authorization code for tokens
            token_url = f'https://login.microsoftonline.com/{mail_server.ms_tenant_id}/oauth2/v2.0/token'
            token_data = {
                'client_id': mail_server.ms_client_id,
                'client_secret': mail_server.ms_client_secret,
                'code': authorization_code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            
            response = requests.post(token_url, data=token_data, timeout=10)
            
            if response.status_code != 200:
                _logger.error(f"Failed to exchange authorization code for tokens: {response.text}")
                raise UserError(_("Failed to authenticate with Microsoft Graph API: %s") % response.text)
                
            token_info = response.json()
            
            # Store the tokens
            mail_server.sudo().write({
                'ms_access_token': token_info.get('access_token'),
                'ms_refresh_token': token_info.get('refresh_token'),
                # Calculate and store expiry time
                'ms_token_expiry': fields.Datetime.now() + datetime.timedelta(seconds=token_info.get('expires_in', 3600))
            })
            
            # Get user email if not already set
            if not mail_server.ms_sender_email:
                try:
                    headers = {
                        'Authorization': f'Bearer {token_info.get("access_token")}',
                        'Content-Type': 'application/json'
                    }
                    user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        mail_server.sudo().write({
                            'ms_sender_email': user_info.get('mail') or user_info.get('userPrincipalName')
                        })
                except Exception as e:
                    _logger.error(f"Error getting user email: {str(e)}")
            
            return {'success': True}
            
        except Timeout:
            error_message = "Timeout during Microsoft authentication"
            _logger.error(error_message)
            raise UserError(_(error_message))
            
        except Exception as e:
            _logger.error(f"Error in auth_oauth_microsoft: {str(e)}")
            raise UserError(_("Error authenticating with Microsoft Graph API: %s") % str(e))
            
    def test_smtp_connection(self):
        """Override the test connection to handle Microsoft Graph API"""
        for server in self:
            if server.use_graph_api:
                if not server.ms_client_id or not server.ms_client_secret or not server.ms_tenant_id:
                    raise UserError(_("Microsoft Graph API credentials not properly configured"))
                    
                if not server.ms_refresh_token:
                    raise UserError(_("Microsoft authentication required. Please authenticate with Microsoft first."))
                    
                try:
                    # Test the connection by refreshing the token and sending a test message
                    server.sudo().refresh_token_if_needed()
                    
                    # Test the actual Graph API connection by calling the /me endpoint
                    headers = {
                        'Authorization': f'Bearer {server.ms_access_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
                    
                    if response.status_code != 200:
                        _logger.error(f"Microsoft Graph API connection test failed: {response.text}")
                        raise UserError(_("Connection Test Failed! API error: %s") % response.text)
                    
                    # If we got this far, the connection is working
                    _logger.info('Microsoft Graph API connection test succeeded for server %s', server.name)
                    
                    # Raise the user-facing notification message
                    raise UserError(_("Connection Test Successful! Microsoft Graph API is properly configured."))
                    
                except Timeout:
                    _logger.error(f"Microsoft Graph API connection test timed out for server {server.name}")
                    raise UserError(_("Connection Test Failed! Request timed out."))
                    
                except UserError as e:
                    # Re-raise user error
                    raise
                except Exception as e:
                    _logger.info("Microsoft Graph API connection test failed for server %s: %s", server.name, e)
                    raise UserError(_("Connection Test Failed! Error: %s") % e)
            else:
                # Call the original method for SMTP servers
                return super(IrMailServer, server).test_smtp_connection()
                
    def button_oauth_microsoft(self):
        """Redirect to Microsoft OAuth authentication"""
        self.ensure_one()
        
        if not self.ms_client_id or not self.ms_client_secret or not self.ms_tenant_id:
            raise UserError(_("Microsoft Graph API credentials not properly configured. Please set client ID, client secret, and tenant ID."))
            
        return {
            'type': 'ir.actions.act_url',
            'url': f'/mail_graph_api/auth?id={self.id}',
            'target': 'self',
        }
        
    def run_graph_api_diagnostics(self):
        """Run diagnostics on the Microsoft Graph API configuration"""
        self.ensure_one()
        
        if not self.use_graph_api:
            raise UserError(_("Graph API is not enabled for this mail server."))
            
        try:
            # Test the connection by refreshing the token
            self.refresh_token_if_needed()
            
            # Test the actual Graph API connection by calling the /me endpoint
            headers = {
                'Authorization': f'Bearer {self.ms_access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise UserError(_("Diagnostics Failed! API error: %s") % response.text)
                
            # If we got this far, the connection is working
            user_info = response.json()
            user_name = user_info.get('displayName', '') or user_info.get('userPrincipalName', '')
            
            raise UserError(_("Diagnostics Successful! Connected as: %s") % user_name)
        except Exception as e:
            raise UserError(_("Diagnostics Failed! Error: %s") % str(e)) 