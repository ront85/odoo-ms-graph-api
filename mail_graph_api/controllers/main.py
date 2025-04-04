import logging
import werkzeug
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
