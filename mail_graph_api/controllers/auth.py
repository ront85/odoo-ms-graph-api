import json
import logging
import requests
import werkzeug
from datetime import datetime, timedelta

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class MicrosoftGraphAuthController(http.Controller):
    
    @http.route('/mail_graph_api/debug', type='http', auth='user', website=True)
    def debug_logs(self, **kw):
        """Show debug logs for Microsoft Graph API"""
        if not request.env.user.has_group('base.group_system'):
            return request.render('mail_graph_api.error_page', {
                'error': _("Only administrators can view debug logs.")
            })
        
        # Get the last 100 logs related to Microsoft Graph API
        logs = request.env['ir.logging'].sudo().search([
            ('name', 'like', 'mail_graph_api'),
            ('level', 'in', ['INFO', 'ERROR', 'WARNING'])
        ], order='create_date desc', limit=100)
        
        return request.render('mail_graph_api.debug_logs', {
            'logs': logs
        })
    
    @http.route('/mail_graph_api/auth', type='http', auth='user', website=True)
    def microsoft_auth(self, **kw):
        """Initiate OAuth flow for Microsoft Graph API"""
        _logger.info("Starting Microsoft Graph API authentication flow")
        _logger.info("Received parameters: %s", kw)
        
        # Check authorization to modify mail server
        if not request.env.user.has_group('base.group_system'):
            _logger.error("User does not have permission to configure mail servers")
            return request.render('mail_graph_api.error_page', {
                'error': _("Only administrators can configure outgoing mail servers.")
            })
        
        # Get the active mail server from the context
        mail_server_id = request.env.context.get('active_id')
        if not mail_server_id:
            _logger.error("No active_id in context")
            return request.render('mail_graph_api.error_page', {
                'error': _("No mail server selected. Please select a mail server first.")
            })
        
        mail_server = request.env['ir.mail_server'].sudo().browse(mail_server_id)
        if not mail_server.exists():
            _logger.error("Mail server not found: %s", mail_server_id)
            return request.render('mail_graph_api.error_page', {
                'error': _("Mail server not found.")
            })
        
        # Use the action_authenticate_microsoft method to handle the authentication
        try:
            result = mail_server.action_authenticate_microsoft()
            if result and result.get('type') == 'ir.actions.act_url':
                return werkzeug.utils.redirect(result['url'])
            else:
                _logger.error("Unexpected result from action_authenticate_microsoft: %s", result)
                return request.render('mail_graph_api.error_page', {
                    'error': _("Failed to initiate authentication process.")
                })
        except Exception as e:
            _logger.error("Error initiating authentication: %s", str(e))
            return request.render('mail_graph_api.error_page', {
                'error': str(e)
            })
    
    @http.route('/mail_graph_api/auth/callback', type='http', auth='user', website=True)
    def microsoft_auth_callback(self, **kw):
        """Handle OAuth callback from Microsoft"""
        _logger.info("Received OAuth callback from Microsoft")
        _logger.info("Callback parameters: %s", kw)
        
        code = kw.get('code')
        state = kw.get('state')  # This contains the mail_server_id
        error = kw.get('error')
        error_description = kw.get('error_description')
        
        if error:
            _logger.error("OAuth error: %s - %s", error, error_description)
            return request.render('mail_graph_api.error_page', {
                'error': error_description
            })
        
        if not code or not state:
            _logger.error("Missing code or state in callback")
            return request.render('mail_graph_api.error_page', {
                'error': _("Missing authorization code or state parameter.")
            })
        
        try:
            mail_server_id = int(state)
        except (ValueError, TypeError) as e:
            _logger.error("Invalid state (mail_server_id): %s - %s", state, str(e))
            return request.render('mail_graph_api.error_page', {
                'error': _("Invalid state parameter.")
            })
        
        mail_server = request.env['ir.mail_server'].sudo().browse(mail_server_id)
        if not mail_server.exists():
            _logger.error("Mail server not found: %s", mail_server_id)
            return request.render('mail_graph_api.error_page', {
                'error': _("Mail server not found.")
            })
        
        # Check authorization to modify mail server
        if not request.env.user.has_group('base.group_system'):
            _logger.error("User does not have permission to configure mail servers")
            return request.render('mail_graph_api.error_page', {
                'error': _("Only administrators can configure outgoing mail servers.")
            })
        
        # Exchange code for tokens
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        token_url = f"https://login.microsoftonline.com/{mail_server.ms_tenant_id}/oauth2/v2.0/token"
        redirect_uri = f"{base_url}/mail_graph_api/auth/callback"
        
        _logger.info("Exchanging code for tokens at %s", token_url)
        _logger.info("Redirect URI: %s", redirect_uri)
        
        payload = {
            'grant_type': 'authorization_code',
            'client_id': mail_server.ms_client_id,
            'client_secret': mail_server.ms_client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'scope': 'https://graph.microsoft.com/Mail.Send offline_access'
        }
        
        try:
            _logger.info("Sending token request with payload: %s", {k: v if k != 'client_secret' else '***' for k, v in payload.items()})
            response = requests.post(token_url, data=payload)
            _logger.info("Token response status: %s", response.status_code)
            
            if response.status_code != 200:
                _logger.error("Token response error: %s", response.text)
                return request.render('mail_graph_api.error_page', {
                    'error': _("Failed to retrieve OAuth token: %s") % response.text
                })
            
            token_data = response.json()
            _logger.info("Token response keys: %s", token_data.keys())
            
            if 'access_token' not in token_data:
                _logger.error("No access token in response: %s", token_data)
                return request.render('mail_graph_api.error_page', {
                    'error': _("No access token received from Microsoft.")
                })
            
            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Update mail server with new tokens
            values = {
                'ms_access_token': token_data.get('access_token'),
                'ms_token_expiry': expiry,
                'use_graph_api': True
            }
            
            # Update refresh token if we got one
            if 'refresh_token' in token_data:
                _logger.info("Received refresh token")
                values['ms_refresh_token'] = token_data.get('refresh_token')
            else:
                _logger.warning("No refresh token in response")
            
            _logger.info("Updating mail server %s with token information", mail_server.id)
            mail_server.write(values)
            
            _logger.info("Authentication successful for mail server %s", mail_server.id)
            
            return request.render('mail_graph_api.success_page', {
                'message': _("Authentication successful! You can now send emails using Microsoft Graph API.")
            })
            
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to retrieve OAuth token: %s", str(e))
            error_message = str(e)
            if hasattr(e, 'response') and e.response:
                error_message += f"\nResponse: {e.response.text}"
            return request.render('mail_graph_api.error_page', {
                'error': _("Failed to retrieve OAuth token: %s") % error_message
            }) 