import logging
import werkzeug
import json
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

class MicrosoftAuthController(http.Controller):
    
    @http.route('/mail_graph_api/auth', type='http', auth='user')
    def microsoft_auth_start(self, **kw):
        """Start the Microsoft OAuth flow"""
        _logger.info("Microsoft Graph API authentication request received")
        
        # Get mail server ID from the request
        mail_server_id = kw.get('id')
        
        if not mail_server_id:
            _logger.error("Microsoft Graph API error: Missing mail server ID")
            return self._render_error(_("No mail server ID provided. Please try again."))
            
        # Find the mail server
        mail_server = request.env['ir.mail_server'].sudo().browse(int(mail_server_id))
        
        if not mail_server.exists() or not mail_server.use_graph_api:
            _logger.error(f"Microsoft Graph API error: Invalid mail server {mail_server_id}")
            return self._render_error(_("Invalid mail server or Graph API not enabled."))
            
        if not mail_server.ms_client_id or not mail_server.ms_tenant_id:
            _logger.error("Microsoft Graph API error: Missing credentials")
            return self._render_error(_("Microsoft Graph API client ID or tenant ID not configured."))
            
        # OAuth state to verify the callback
        state = mail_server_id
        
        # Build the authorization URL
        redirect_uri = request.httprequest.url_root.rstrip('/') + '/mail_graph_api/auth/callback'
        
        auth_url = f"https://login.microsoftonline.com/{mail_server.ms_tenant_id}/oauth2/v2.0/authorize"
        auth_url += f"?client_id={mail_server.ms_client_id}"
        auth_url += "&response_type=code"
        auth_url += f"&redirect_uri={redirect_uri}"
        auth_url += "&scope=https://graph.microsoft.com/.default offline_access"
        auth_url += f"&state={state}"
        auth_url += "&response_mode=query"
        
        _logger.info(f"Redirecting to Microsoft OAuth: {auth_url}")
        
        return werkzeug.utils.redirect(auth_url)
        
    @http.route('/mail_graph_api/auth/callback', type='http', auth='user')
    def microsoft_auth_callback(self, **kw):
        """Handle the callback from Microsoft OAuth"""
        _logger.info(f"Microsoft OAuth callback received: {kw}")
        
        error = kw.get('error')
        if error:
            error_description = kw.get('error_description', '')
            _logger.error(f"Microsoft OAuth error: {error} - {error_description}")
            return self._render_error(f"{error}: {error_description}")
            
        code = kw.get('code')
        state = kw.get('state')  # This contains the mail server ID
        
        if not code:
            _logger.error("No authorization code received from Microsoft")
            return self._render_error(_("No authorization code received from Microsoft."))
        
        if not state:
            _logger.error("No state parameter received")
            return self._render_error(_("No state parameter received. Authentication failed."))
            
        try:
            mail_server_id = int(state)
            mail_server = request.env['ir.mail_server'].sudo().browse(mail_server_id)
            
            if not mail_server.exists():
                _logger.error(f"Mail server not found: {mail_server_id}")
                return self._render_error(_("Mail server not found."))
            
            # Exchange the code for access token
            redirect_uri = request.httprequest.url_root.rstrip('/') + '/mail_graph_api/auth/callback'
            
            from datetime import datetime, timedelta
            import requests
            
            token_url = f"https://login.microsoftonline.com/{mail_server.ms_tenant_id}/oauth2/v2.0/token"
            token_data = {
                'client_id': mail_server.ms_client_id,
                'client_secret': mail_server.ms_client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            
            response = requests.post(token_url, data=token_data, timeout=10)
            
            if response.status_code != 200:
                _logger.error(f"Failed to exchange authorization code for tokens: {response.text}")
                return self._render_error(_("Failed to authenticate with Microsoft Graph API: %s") % response.text)
                
            token_info = response.json()
            
            # Store the tokens
            mail_server.sudo().write({
                'ms_access_token': token_info.get('access_token'),
                'ms_refresh_token': token_info.get('refresh_token'),
                # Calculate and store expiry time
                'ms_token_expiry': datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))
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
            
            _logger.info(f"Microsoft OAuth authentication successful for server {mail_server.id}")
            return self._render_success(_("Authentication successful! You can now send emails using Microsoft Graph API."))
            
        except ValueError:
            _logger.error(f"Invalid state (mail_server_id): {state}")
            return self._render_error(_("Invalid state parameter."))
            
        except Exception as e:
            _logger.error(f"Error in auth_oauth_microsoft: {str(e)}")
            return self._render_error(_("Error authenticating with Microsoft Graph API: %s") % str(e))

    def _render_error(self, error_message):
        """Simple error page renderer that doesn't rely on website layout"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Microsoft Graph API - Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .error {{ color: red; padding: 10px; border: 1px solid red; background-color: #ffeeee; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h2>Microsoft Graph API Error</h2>
            <div class="error">{error_message}</div>
            <a href="/web#action=mail.ir_mail_server_list_action" class="button">Return to Mail Server Configuration</a>
        </body>
        </html>
        """
        return http.Response(html, content_type='text/html')
        
    def _render_success(self, success_message):
        """Simple success page renderer that doesn't rely on website layout"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Microsoft Graph API - Success</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .success {{ color: green; padding: 10px; border: 1px solid green; background-color: #eeffee; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h2>Microsoft Graph API Success</h2>
            <div class="success">{success_message}</div>
            <a href="/web#action=mail.ir_mail_server_list_action" class="button">Return to Mail Server Configuration</a>
        </body>
        </html>
        """
        return http.Response(html, content_type='text/html')

class MicrosoftGraphDebugController(http.Controller):
    
    @http.route('/mail_graph_api/debug', type='http', auth='user')
    def graph_api_debug(self, **kw):
        """Display debug logs for Microsoft Graph API"""
        _logger.info("Accessing Graph API debug logs")
        
        # Check if user has access
        if not request.env.user.has_group('base.group_system'):
            return self._render_error(_("Only administrators can view debug logs."))
        
        # Get the most recent 100 logs related to Microsoft Graph API
        logs = request.env['ir.logging'].sudo().search([
            ('name', 'ilike', '%mail_graph_api%'),
            ('level', 'in', ['INFO', 'ERROR', 'WARNING'])
        ], order='create_date desc', limit=100)
        
        # Format logs into HTML
        log_html = "<h2>Microsoft Graph API Debug Logs</h2>"
        log_html += "<p>Showing the last 100 log entries related to Microsoft Graph API.</p>"
        
        if logs:
            log_html += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
            log_html += "<tr><th>Date</th><th>Level</th><th>Message</th></tr>"
            
            for log in logs:
                color = {
                    'INFO': 'blue',
                    'WARNING': 'orange',
                    'ERROR': 'red'
                }.get(log.level, 'black')
                
                log_html += f"<tr>"
                log_html += f"<td>{log.create_date}</td>"
                log_html += f"<td style='color: {color};'>{log.level}</td>"
                log_html += f"<td>{log.message}</td>"
                log_html += "</tr>"
                
            log_html += "</table>"
        else:
            log_html += "<p>No logs found. Try enabling debug mode and sending a test email.</p>"
        
        # Create a custom response with the logs
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Microsoft Graph API - Debug Logs</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ width: 100%; }}
                th {{ background-color: #f2f2f2; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            {log_html}
            <a href="/web#action=mail.ir_mail_server_list_action" class="button">Return to Mail Server Configuration</a>
        </body>
        </html>
        """
        return http.Response(html, content_type='text/html')
        
    def _render_error(self, error_message):
        """Simple error page renderer that doesn't rely on website layout"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Microsoft Graph API - Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .error {{ color: red; padding: 10px; border: 1px solid red; background-color: #ffeeee; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h2>Microsoft Graph API Error</h2>
            <div class="error">{error_message}</div>
            <a href="/web#action=mail.ir_mail_server_list_action" class="button">Return to Mail Server Configuration</a>
        </body>
        </html>
        """
        return http.Response(html, content_type='text/html')
