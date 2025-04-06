import logging
import werkzeug
import json
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

class MicrosoftAuthController(http.Controller):
    
    @http.route('/microsoft/auth', type='http', auth='user')
    def microsoft_auth_start(self, **kw):
        """Start the Microsoft OAuth flow"""
        _logger.info("Starting Microsoft OAuth flow")
        
        # Find a mail server that uses Microsoft Graph API
        mail_server = request.env['ir.mail_server'].sudo().search([('use_graph_api', '=', True)], limit=1)
        
        if not mail_server:
            return werkzeug.utils.redirect('/web#id=&action=mail.action_email_configure')
            
        if not mail_server.ms_client_id or not mail_server.ms_tenant_id:
            return request.render('mail_graph_api.ms_auth_error', {
                'error': _("Microsoft Graph API client ID or tenant ID not configured.")
            })
            
        # OAuth state to verify the callback
        state = {
            'model': 'ir.mail_server',
            'id': mail_server.id,
        }
        
        # Store in session
        request.session['microsoft_oauth_state'] = state
        
        # Build the authorization URL
        redirect_uri = request.httprequest.url_root.rstrip('/') + '/microsoft/auth/callback'
        
        auth_url = f"https://login.microsoftonline.com/{mail_server.ms_tenant_id}/oauth2/v2.0/authorize"
        auth_url += f"?client_id={mail_server.ms_client_id}"
        auth_url += "&response_type=code"
        auth_url += f"&redirect_uri={redirect_uri}"
        auth_url += "&scope=https://graph.microsoft.com/.default offline_access"
        auth_url += "&response_mode=query"
        
        _logger.info("Redirecting to Microsoft OAuth: %s", auth_url)
        
        return werkzeug.utils.redirect(auth_url)
        
    @http.route('/microsoft/auth/callback', type='http', auth='user')
    def microsoft_auth_callback(self, **kw):
        """Handle the callback from Microsoft OAuth"""
        _logger.info("Received Microsoft OAuth callback: %s", kw)
        
        error = kw.get('error')
        if error:
            error_description = kw.get('error_description', '')
            _logger.error("Microsoft OAuth error: %s - %s", error, error_description)
            return request.render('mail_graph_api.ms_auth_error', {
                'error': f"{error}: {error_description}"
            })
            
        code = kw.get('code')
        if not code:
            _logger.error("No authorization code received from Microsoft")
            return request.render('mail_graph_api.ms_auth_error', {
                'error': _("No authorization code received from Microsoft.")
            })
            
        # Verify state
        state = request.session.get('microsoft_oauth_state')
        if not state:
            _logger.error("No OAuth state found in session")
            return request.render('mail_graph_api.ms_auth_error', {
                'error': _("Authentication failed: Invalid state.")
            })
            
        # Exchange the code for access token
        redirect_uri = request.httprequest.url_root.rstrip('/') + '/microsoft/auth/callback'
        
        try:
            result = request.env['ir.mail_server'].sudo().auth_oauth_microsoft(code, redirect_uri)
            _logger.info("Microsoft OAuth authentication successful: %s", result)
            
            # Redirect back to mail server configuration
            return werkzeug.utils.redirect('/web#id=&action=mail.action_email_configure&view_type=list')
            
        except Exception as e:
            _logger.error("Error in Microsoft OAuth callback: %s", str(e))
            return request.render('mail_graph_api.ms_auth_error', {
                'error': str(e)
            })

class MicrosoftGraphDebugController(http.Controller):
    
    @http.route('/mail_graph_api/debug', type='http', auth='user')
    def graph_api_debug(self, **kw):
        """Display debug logs for Microsoft Graph API"""
        _logger.info("Accessing Graph API debug logs")
        
        # Get the most recent 100 logs related to Microsoft Graph API
        logs = request.env['ir.logging'].sudo().search([
            ('name', 'ilike', '%mail_graph_api%'),
            ('level', 'in', ['INFO', 'ERROR', 'WARNING'])
        ], order='create_date desc', limit=100)
        
        return request.render('mail_graph_api.debug_logs', {
            'logs': logs
        })
        
    @http.route('/mail_graph_api/system_info', type='http', auth='user')
    def system_info(self, **kw):
        """Display system information relevant to Microsoft Graph API"""
        _logger.info("Accessing Graph API system info")
        
        # Get mail servers that use Graph API
        mail_servers = request.env['ir.mail_server'].sudo().search([
            ('use_graph_api', '=', True)
        ])
        
        # Get system parameters related to mail
        mail_params = request.env['ir.config_parameter'].sudo().search([
            ('key', 'ilike', '%mail%')
        ])
        
        # Get Odoo version
        version_info = request.env['ir.module.module'].sudo().search([
            ('name', '=', 'base')
        ], limit=1)
        
        # Get information about mail.mail records
        mail_stats = {
            'outgoing': request.env['mail.mail'].sudo().search_count([('state', '=', 'outgoing')]),
            'sent': request.env['mail.mail'].sudo().search_count([('state', '=', 'sent')]),
            'exception': request.env['mail.mail'].sudo().search_count([('state', '=', 'exception')]),
            'graph_api_attempted': request.env['mail.mail'].sudo().search_count([('graph_api_attempted', '=', True)]),
        }
        
        # Get recent failures
        failed_mails = request.env['mail.mail'].sudo().search([
            ('state', '=', 'exception')
        ], order='create_date desc', limit=10)
        
        system_info = {
            'odoo_version': version_info.installed_version if version_info else 'Unknown',
            'mail_servers': [{
                'name': server.name,
                'ms_sender_email': server.ms_sender_email,
                'token_expiry': server.ms_token_expiry,
                'has_access_token': bool(server.ms_access_token),
                'has_refresh_token': bool(server.ms_refresh_token),
            } for server in mail_servers],
            'mail_parameters': [{
                'key': param.key,
                'value': param.value
            } for param in mail_params],
            'mail_stats': mail_stats,
            'failed_mails': [{
                'id': mail.id,
                'subject': mail.subject,
                'date': mail.create_date,
                'reason': mail.failure_reason
            } for mail in failed_mails]
        }
        
        return request.render('mail_graph_api.system_info', {
            'system_info': system_info
        })
        
    @http.route('/mail_graph_api/test_connection/<int:server_id>', type='http', auth='user')
    def test_connection(self, server_id, **kw):
        """Test the connection to Microsoft Graph API and return JSON result"""
        _logger.info("Testing Graph API connection for server %s", server_id)
        
        server = request.env['ir.mail_server'].sudo().browse(server_id)
        if not server.exists() or not server.use_graph_api:
            return json.dumps({
                'success': False,
                'message': 'Server not found or Graph API not enabled'
            })
            
        try:
            # Set debug mode
            server.debug_mode = True
            
            # Run the test
            token = server._get_oauth_token()
            
            if not token:
                return json.dumps({
                    'success': False,
                    'message': 'Failed to get access token'
                })
                
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            import requests
            user_url = f"https://graph.microsoft.com/v1.0/users/{server.ms_sender_email}"
            response = requests.get(user_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return json.dumps({
                    'success': True,
                    'message': f"Connection successful! Found user: {user_data.get('displayName', 'Unknown')}"
                })
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return json.dumps({
                    'success': False,
                    'message': f"API error: {error_msg}"
                })
                
        except Exception as e:
            _logger.error("Error testing connection: %s", str(e))
            return json.dumps({
                'success': False,
                'message': f"Error: {str(e)}"
            })
