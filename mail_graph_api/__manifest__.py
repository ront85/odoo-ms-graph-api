{
    'name': 'Microsoft Graph API Mail Integration',
    'version': '1.0.0',
    'category': 'Mail',
    'summary': 'Send emails using Microsoft Graph API',
    'description': """
Microsoft Graph API Mail Integration
====================================

This module allows sending emails via Microsoft Graph API instead of SMTP.
It integrates with Microsoft 365 to send emails using OAuth2 authentication.

Features:
- Configure Outlook/Microsoft 365 for sending emails
- OAuth2 authentication with Microsoft
- Send emails using Microsoft Graph API
- Automatic token refresh
""",
    'author': 'Your Company',
    'website': 'https://www.example.com',
    'depends': ['base', 'mail'],
    'data': [
        'views/ir_mail_server_views.xml',
        'views/ms_auth_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 