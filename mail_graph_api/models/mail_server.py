import json
import logging
import requests
import base64
import html
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    use_graph_api = fields.Boolean(
        string="Use Microsoft Graph API",
        help="Enable to use Microsoft Graph API instead of SMTP",
        default=False
    )
    ms_client_id = fields.Char(
        string="Client ID",
        help="Azure App Client ID"
    )
    ms_client_secret = fields.Char(
        string="Client Secret",
        help="Azure App Client Secret"
    )
    ms_tenant_id = fields.Char(
        string="Tenant ID",
        help="Azure Directory (Tenant) ID"
    )
    ms_sender_email = fields.Char(
        string="Sender Email",
        help="Email address to send from using Microsoft Graph API"
    )
    ms_access_token = fields.Char(
        string="Access Token",
        help="OAuth2 Access Token",
        readonly=True,
        copy=False
    )
    ms_refresh_token = fields.Char(
        string="Refresh Token",
        help="OAuth2 Refresh Token",
        readonly=True,
        copy=False
    )
    ms_token_expiry = fields.Datetime(
        string="Token Expiry",
        help="OAuth2 Token Expiry Date",
        readonly=True,
        copy=False
    )
    fallback_to_smtp = fields.Boolean(
        string="Fallback to SMTP",
        help="If enabled, emails will be sent via SMTP if Graph API fails",
        default=True
    )
    graph_api_logs = fields.Html(
        string="Graph API Logs",
        compute="_compute_graph_api_logs",
        help="Recent logs related to Microsoft Graph API",
        readonly=True
    )

    @api.depends('use_graph_api')
    def _compute_graph_api_logs(self):
        """Compute the logs related to Microsoft Graph API"""
        for server in self:
            try:
                if server.use_graph_api:
                    # Get the most recent 100 logs related to Microsoft Graph API
                    logs = self.env['ir.logging'].sudo().search([
                        ('name', 'ilike', '%mail_graph_api%'),
                        ('level', 'in', ['INFO', 'ERROR', 'WARNING'])
                    ], order='create_date desc', limit=100)
                    
                    if not logs:
                        server.graph_api_logs = "<p class='text-muted'>No logs found. Try sending an email or authenticating with Microsoft.</p>"
                        continue
                    
                    # Format logs in HTML with better styling
                    log_html = """
                    <div class="o_mail_thread" style="max-height: 500px; overflow-y: auto;">
                        <div class="o_thread_message_list">
                    """
                    
                    for log in logs:
                        level_class = {
                            'INFO': 'text-info',
                            'WARNING': 'text-warning',
                            'ERROR': 'text-danger'
                        }.get(log.level, '')
                        
                        level_icon = {
                            'INFO': 'fa-info-circle',
                            'WARNING': 'fa-exclamation-triangle',
                            'ERROR': 'fa-times-circle'
                        }.get(log.level, 'fa-info-circle')
                        
                        formatted_date = log.create_date.strftime('%Y-%m-%d %H:%M:%S')
                        escaped_message = html.escape(log.message).replace('\n', '<br/>')
                        
                        log_html += f"""
                        <div class="o_thread_message" style="margin-bottom: 10px; border-bottom: 1px solid #eeeeee; padding-bottom: 5px;">
                            <div class="o_thread_message_sidebar" style="display: inline-block; vertical-align: top; margin-right: 10px;">
                                <div class="o_thread_message_sidebar_image">
                                    <i class="fa {level_icon} {level_class}" title="{log.level}" style="font-size: 1.3em;"></i>
                                </div>
                            </div>
                            <div class="o_thread_message_core" style="display: inline-block; width: calc(100% - 30px);">
                                <p class="o_mail_info">
                                    <strong class="{level_class}">{log.level}</strong> • <span class="text-muted">{formatted_date}</span>
                                </p>
                                <div class="o_thread_message_content" style="word-wrap: break-word;">
                                    <p>{escaped_message}</p>
                                </div>
                            </div>
                        </div>
                        """
                    
                    log_html += """
                        </div>
                    </div>
                    """
                    
                    server.graph_api_logs = log_html
                else:
                    server.graph_api_logs = "<p class='text-muted'>Enable Microsoft Graph API to view logs.</p>"
            except Exception as e:
                _logger.error("Error computing graph API logs: %s", str(e))
                server.graph_api_logs = f"<p class='text-danger'>Error loading logs: {html.escape(str(e))}</p>"

    @api.onchange('use_graph_api')
    def _onchange_use_graph_api(self):
        pass

    def _get_oauth_token(self):
        """Get a valid OAuth token, refreshing if necessary"""
        self.ensure_one()
        
        _logger.info("Getting OAuth token for mail server %s", self.id)
        
        # Check if token is still valid
        if self.ms_access_token and self.ms_token_expiry:
            expiry = fields.Datetime.from_string(self.ms_token_expiry)
            if expiry > datetime.now() + timedelta(minutes=5):
                _logger.info("Using existing token (valid until %s)", expiry)
                return self.ms_access_token
        
        # Token is expired or missing, refresh it
        _logger.info("Token expired or missing, refreshing...")
        return self._refresh_oauth_token()
    
    def _refresh_oauth_token(self):
        """Refresh the OAuth token using client credentials flow"""
        self.ensure_one()
        
        if not self.ms_client_id or not self.ms_client_secret or not self.ms_tenant_id:
            _logger.error("Microsoft Graph API credentials are incomplete")
            raise UserError(_("Microsoft Graph API credentials are incomplete. Please check Client ID, Client Secret, and Tenant ID."))
        
        token_url = f"https://login.microsoftonline.com/{self.ms_tenant_id}/oauth2/v2.0/token"
        
        # If we have a refresh token, use refresh token grant
        if self.ms_refresh_token:
            _logger.info("Using refresh token grant")
            payload = {
                'grant_type': 'refresh_token',
                'client_id': self.ms_client_id,
                'client_secret': self.ms_client_secret,
                'refresh_token': self.ms_refresh_token,
                'scope': 'https://graph.microsoft.com/Mail.Send offline_access'
            }
        else:
            # Fall back to client credentials grant
            _logger.info("Using client credentials grant")
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.ms_client_id,
                'client_secret': self.ms_client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            }
        
        try:
            _logger.info("Sending token request to %s", token_url)
            response = requests.post(token_url, data=payload, timeout=10)
            _logger.info("Token response status: %s", response.status_code)
            
            if response.status_code != 200:
                _logger.error("Token response error: %s", response.text)
            
            response.raise_for_status()
            token_data = response.json()
            
            # Update token information
            values = {
                'ms_access_token': token_data.get('access_token'),
                'ms_token_expiry': fields.Datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            }
            
            # Update refresh token if we got a new one
            if token_data.get('refresh_token'):
                _logger.info("Received new refresh token")
                values['ms_refresh_token'] = token_data.get('refresh_token')
            
            _logger.info("Updating token information in database")
            self.write(values)
            
            return token_data.get('access_token')
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to refresh OAuth token: %s", str(e))
            if hasattr(e, 'response') and e.response:
                _logger.error("Response: %s", e.response.text)
            raise UserError(_("Failed to authenticate with Microsoft Graph API: %s") % str(e))
    
    def test_graph_api_connection(self):
        """Test the connection to Microsoft Graph API"""
        self.ensure_one()
        
        _logger.info("Testing Graph API connection for mail server %s", self.id)
        
        try:
            token = self._get_oauth_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # First try with Mail.Send permission
            _logger.info("Testing sendMail endpoint with user %s", self.ms_sender_email)
            test_message = {
                "message": {
                    "subject": "Test Connection",
                    "body": {
                        "contentType": "Text",
                        "content": "This is a test message."
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": self.ms_sender_email
                            }
                        }
                    ]
                },
                "saveToSentItems": "false"
            }
            
            url = f"{GRAPH_API_ENDPOINT}/users/{self.ms_sender_email}/sendMail"
            _logger.info("Sending test request to %s", url)
            
            response = requests.post(url, headers=headers, json=test_message, timeout=10)
            _logger.info("Test response status: %s", response.status_code)
            
            if response.status_code == 202:
                _logger.info("Test successful")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Connection Test Succeeded"),
                        'message': _("Successfully connected to Microsoft Graph API."),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                _logger.error("Test failed with status %s: %s", response.status_code, response.text)
                error_message = f"Status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data and 'message' in error_data['error']:
                        error_message = f"{error_message}: {error_data['error']['message']}"
                except:
                    if hasattr(response, 'text'):
                        error_message = f"{error_message}: {response.text}"
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Connection Test Failed"),
                        'message': error_message,
                        'sticky': True,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.error("Test connection exception: %s", str(e))
            error_message = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data and 'message' in error_data['error']:
                        error_message = f"{error_message}: {error_data['error']['message']}"
                except:
                    if hasattr(e.response, 'text'):
                        error_message = f"{error_message}: {e.response.text}"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Connection Test Failed"),
                    'message': error_message,
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_debug=False, smtp_session=None):
        """Override to use Microsoft Graph API if enabled"""
        # Add debug log to verify method is being called
        _logger.info("=== MAIL_GRAPH_API: send_email method called ===")
        
        # Log message details for debugging
        _logger.info("Message headers: %s", message.items())
        _logger.info("Mail server ID: %s, SMTP server: %s", mail_server_id, smtp_server)
        
        # Find the appropriate mail server to use
        mail_server = None
        if mail_server_id:
            mail_server = self.browse(mail_server_id)
            _logger.info("Using explicitly specified mail server ID: %s, Graph API enabled: %s", 
                         mail_server_id, mail_server.use_graph_api if mail_server else "N/A")
        elif not smtp_server:
            _logger.info("No mail server ID or SMTP server specified, searching for Graph API enabled server")
            mail_server = self.sudo().search([('use_graph_api', '=', True)], order='sequence', limit=1)
            if mail_server:
                _logger.info("Found Graph API server ID: %s", mail_server.id)
            else:
                _logger.info("No Graph API enabled mail server found")
        else:
            _logger.info("Using SMTP server settings directly: %s:%s", smtp_server, smtp_port)
        
        if mail_server and mail_server.use_graph_api:
            _logger.info("=== MAIL_GRAPH_API: Using Graph API mail server ID %s ===", mail_server.id)
            try:
                _logger.debug("Starting email sending process for mail server %s", mail_server.id)

                # Ensure we have a valid token
                mail_server.refresh_token_if_needed()
                if not mail_server.ms_access_token:
                    _logger.error("No access token available - authentication may be required")
                    # Fall back to super method if specified
                    if mail_server.fallback_to_smtp:
                        _logger.info("Falling back to standard SMTP")
                        return super(IrMailServer, self).send_email(
                            message, mail_server_id=mail_server_id, smtp_server=smtp_server,
                            smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password,
                            smtp_encryption=smtp_encryption, smtp_debug=smtp_debug, smtp_session=smtp_session
                        )
                    raise UserError(_("Microsoft Graph API authentication required. Please authenticate in the mail server settings."))

                # Extract email data from the message
                from_email = mail_server.ms_sender_email
                to_list = message.get_all('To', [])
                subject = message.get('Subject', '')
                
                # Get the message payload - handling different message types
                if message.is_multipart():
                    _logger.info("Processing multipart message")
                    for part in message.walk():
                        content_type = part.get_content_type()
                        _logger.info("Message part content type: %s", content_type)
                        if content_type == 'text/html':
                            body = part.get_payload(decode=True).decode()
                            content_type = 'HTML'
                            break
                        elif content_type == 'text/plain':
                            body = part.get_payload(decode=True).decode()
                            content_type = 'Text'
                    else:
                        # If no text/html or text/plain part was found, use the first part
                        body = message.get_payload(0).get_payload(decode=True).decode()
                        content_type = 'Text'
                else:
                    _logger.info("Processing single part message")
                    body = message.get_payload(decode=True).decode()
                    content_type = 'Text'
                    if message.get_content_type() == 'text/html':
                        content_type = 'HTML'

                _logger.debug("Email details - From: %s, To: %s, Subject: %s, Content-Type: %s", 
                             from_email, to_list, subject, content_type)

                # Prepare the Graph API request
                graph_url = f"{GRAPH_API_ENDPOINT}/users/{from_email}/sendMail"
                headers = {
                    'Authorization': f'Bearer {mail_server.ms_access_token}',
                    'Content-Type': 'application/json'
                }

                # Prepare the email payload
                email_payload = {
                    "message": {
                        "subject": subject,
                        "body": {
                            "contentType": content_type,
                            "content": body
                        },
                        "toRecipients": [{"emailAddress": {"address": email}} for email in to_list],
                        "from": {
                            "emailAddress": {
                                "address": from_email
                            }
                        }
                    },
                    "saveToSentItems": "true"
                }

                _logger.debug("Sending email payload to Graph API")

                # Send the request to Graph API
                response = requests.post(graph_url, headers=headers, json=email_payload, timeout=30)
                _logger.debug("Email sent response status: %s", response.status_code)

                if response.status_code not in [200, 202]:
                    error_message = f"Failed to send email: {response.text}"
                    _logger.error(error_message)
                    
                    # Fall back to super method if specified
                    if mail_server.fallback_to_smtp:
                        _logger.info("Falling back to standard SMTP")
                        return super(IrMailServer, self).send_email(
                            message, mail_server_id=mail_server_id, smtp_server=smtp_server,
                            smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password,
                            smtp_encryption=smtp_encryption, smtp_debug=smtp_debug, smtp_session=smtp_session
                        )
                    
                    raise UserError(error_message)

                _logger.info("Email sent successfully via Microsoft Graph API")
                return message.get('Message-Id')

            except Exception as e:
                _logger.error("Error sending email via Microsoft Graph API: %s", str(e), exc_info=True)
                
                # Fall back to super method if specified
                if mail_server and mail_server.fallback_to_smtp:
                    _logger.info("Exception occurred, falling back to standard SMTP")
                    return super(IrMailServer, self).send_email(
                        message, mail_server_id=mail_server_id, smtp_server=smtp_server,
                        smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password,
                        smtp_encryption=smtp_encryption, smtp_debug=smtp_debug, smtp_session=smtp_session
                    )
                
                raise UserError(_("Failed to send email: %s") % str(e))
        
        return super(IrMailServer, self).send_email(
            message, mail_server_id=mail_server_id, smtp_server=smtp_server,
            smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password,
            smtp_encryption=smtp_encryption, smtp_debug=smtp_debug, smtp_session=smtp_session
        )

    def action_authenticate_microsoft(self):
        """Redirect to Microsoft OAuth authentication page"""
        self.ensure_one()
        
        if not self.ms_client_id or not self.ms_tenant_id:
            raise UserError(_("Client ID and Tenant ID are required for Microsoft Graph API authentication."))
        
        # Log the authentication attempt
        _logger.info("Starting Microsoft Graph API authentication for mail server %s", self.id)
        
        # Construct the authentication URL
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_uri = f"{base_url}/mail_graph_api/auth/callback"
        
        # Use delegated permissions for Mail.Send
        scope = "https://graph.microsoft.com/Mail.Send offline_access"
        
        auth_url = f"https://login.microsoftonline.com/{self.ms_tenant_id}/oauth2/v2.0/authorize"
        auth_url += f"?client_id={self.ms_client_id}"
        auth_url += f"&response_type=code"
        auth_url += f"&redirect_uri={redirect_uri}"
        auth_url += f"&scope={scope}"
        auth_url += f"&state={self.id}"
        auth_url += f"&prompt=consent"  # Force consent screen to appear
        
        _logger.info("Redirecting to Microsoft authentication URL for mail server %s", self.id)
        
        # Return an action to redirect to the authentication URL
        return {
            'type': 'ir.actions.act_url',
            'url': auth_url,
            'target': 'self',
        }

    def refresh_token_if_needed(self):
        """Refresh the access token if it's expired or about to expire"""
        self.ensure_one()
        
        if not self.use_graph_api:
            return False
        
        # Check if token is expired or about to expire (within 5 minutes)
        now = datetime.now()
        expiry_threshold = now + timedelta(minutes=5)
        
        if not self.ms_token_expiry or self.ms_token_expiry <= expiry_threshold:
            _logger.info("Token expired or about to expire for mail server %s, refreshing...", self.id)
            
            # If we have a refresh token, use it
            if self.ms_refresh_token:
                token_url = f"https://login.microsoftonline.com/{self.ms_tenant_id}/oauth2/v2.0/token"
                payload = {
                    'grant_type': 'refresh_token',
                    'client_id': self.ms_client_id,
                    'client_secret': self.ms_client_secret,
                    'refresh_token': self.ms_refresh_token,
                    'scope': 'https://graph.microsoft.com/Mail.Send offline_access'
                }
                
                try:
                    _logger.info("Sending refresh token request for mail server %s", self.id)
                    response = requests.post(token_url, data=payload, timeout=10)
                    
                    if response.status_code != 200:
                        _logger.error("Failed to refresh token: %s", response.text)
                        # If refresh token fails, try client credentials
                        return self._refresh_oauth_token()
                    
                    token_data = response.json()
                    
                    if 'access_token' not in token_data:
                        _logger.error("No access token in refresh response: %s", token_data)
                        return self._refresh_oauth_token()
                    
                    # Calculate expiry time
                    expires_in = token_data.get('expires_in', 3600)
                    expiry = now + timedelta(seconds=expires_in)
                    
                    # Update tokens
                    values = {
                        'ms_access_token': token_data.get('access_token'),
                        'ms_token_expiry': expiry
                    }
                    
                    # Update refresh token if we got a new one
                    if 'refresh_token' in token_data:
                        values['ms_refresh_token'] = token_data.get('refresh_token')
                    
                    self.write(values)
                    _logger.info("Successfully refreshed token for mail server %s", self.id)
                    return True
                    
                except requests.exceptions.RequestException as e:
                    _logger.error("Error refreshing token: %s", str(e))
                    # If refresh token fails, try client credentials
                    return self._refresh_oauth_token()
            else:
                # No refresh token, use client credentials
                return self._refresh_oauth_token()
        
        return True

    def test_smtp_connection(self):
        """Override to test Microsoft Graph API connection if enabled"""
        # Add debug log to verify method is being called
        _logger.info("=== MAIL_GRAPH_API: test_smtp_connection method called ===")
        
        for server in self:
            if server.use_graph_api:
                _logger.info("Testing Microsoft Graph API connection for mail server %s", server.id)
                
                if not server.ms_access_token or not server.ms_sender_email:
                    raise UserError(_("Microsoft Graph API is enabled but no access token or sender email is configured."))
                
                # Refresh token if needed
                if not server.refresh_token_if_needed():
                    raise UserError(_("Failed to refresh Microsoft Graph API token. Please authenticate again."))
                
                # Test connection by sending a test email to the Graph API endpoint
                graph_url = f"{GRAPH_API_ENDPOINT}/users/{server.ms_sender_email}/sendMail"
                headers = {
                    'Authorization': f'Bearer {server.ms_access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Simple test message
                test_message = {
                    "message": {
                        "subject": "Test Connection",
                        "body": {
                            "contentType": "Text",
                            "content": "This is a test message to verify the Microsoft Graph API connection."
                        },
                        "toRecipients": [
                            {
                                "emailAddress": {
                                    "address": server.ms_sender_email
                                }
                            }
                        ]
                    },
                    "saveToSentItems": "false"
                }
                
                try:
                    _logger.info("Sending test message to Graph API for mail server %s", server.id)
                    response = requests.post(graph_url, headers=headers, json=test_message, timeout=10)
                    
                    if response.status_code == 202 or response.status_code == 200:
                        _logger.info("Microsoft Graph API connection test successful for mail server %s", server.id)
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Connection Test Successful!'),
                                'message': _('Your Microsoft Graph API connection works properly.'),
                                'sticky': False,
                                'type': 'success',
                            }
                        }
                    else:
                        error_message = f"Status code: {response.status_code}"
                        try:
                            error_data = response.json()
                            if 'error' in error_data:
                                error_message += f"\nError: {error_data['error'].get('code', '')}"
                                error_message += f"\nMessage: {error_data['error'].get('message', '')}"
                        except:
                            error_message += f"\nResponse: {response.text}"
                        
                        _logger.error("Microsoft Graph API connection test failed: %s", error_message)
                        raise UserError(_("Microsoft Graph API connection test failed: %s") % error_message)
                        
                except requests.exceptions.RequestException as e:
                    _logger.error("Error testing Microsoft Graph API connection: %s", str(e))
                    raise UserError(_("Error testing Microsoft Graph API connection: %s") % str(e))
            else:
                # Use the standard SMTP test for non-Graph API servers
                return super(IrMailServer, self).test_smtp_connection() 