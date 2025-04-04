import logging
import json
import datetime
import requests
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
                
                response = requests.post(token_url, data=token_data, timeout=30)
                
                if response.status_code != 200:
                    _logger.error(f"Failed to refresh token: {response.text}")
                    raise UserError(_("Failed to refresh Microsoft Graph API token: %s") % response.text)
                    
                token_info = response.json()
                
                # Update the tokens
                self.ms_access_token = token_info.get('access_token')
                # Only update refresh token if a new one was provided
                if token_info.get('refresh_token'):
                    self.ms_refresh_token = token_info.get('refresh_token')
                # Calculate and store expiry time
                expires_in = token_info.get('expires_in', 3600)  # Default to 1 hour if not specified
                self.ms_token_expiry = fields.Datetime.now() + datetime.timedelta(seconds=expires_in)
                
                _logger.info("Microsoft Graph API token refreshed successfully")
                
            except Exception as e:
                _logger.error(f"Error refreshing Microsoft Graph API token: {str(e)}")
                raise UserError(_("Error refreshing Microsoft Graph API token: %s") % str(e))
                
        return True
    
    @api.model
    def auth_oauth_microsoft(self, authorization_code, redirect_uri):
        """Exchange authorization code for access and refresh tokens"""
        
        # Find a mail server that uses Microsoft Graph API
        mail_server = self.search([('use_graph_api', '=', True)], limit=1)
        
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
            
            response = requests.post(token_url, data=token_data, timeout=30)
            
            if response.status_code != 200:
                _logger.error(f"Failed to exchange authorization code for tokens: {response.text}")
                raise UserError(_("Failed to authenticate with Microsoft Graph API: %s") % response.text)
                
            token_info = response.json()
            
            # Store the tokens
            mail_server.write({
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
                    user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers, timeout=30)
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        mail_server.ms_sender_email = user_info.get('mail') or user_info.get('userPrincipalName')
                except Exception as e:
                    _logger.error(f"Error getting user email: {str(e)}")
            
            return {'success': True}
            
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
                    # Test the connection by refreshing the token
                    server.refresh_token_if_needed()
                    
                    # If we got this far, the connection is working
                    _logger.info('Microsoft Graph API connection test succeeded for server %s', server.name)
                    
                    # Raise the user-facing notification message
                    raise UserError(_("Connection Test Successful! Microsoft Graph API is properly configured."))
                    
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
            'url': '/microsoft/auth',
            'target': 'self',
        } 