{
    'name': 'Microsoft Graph API Mail Gateway',
    'version': '1.0',
    'category': 'Hidden/Tools',
    'summary': 'Send emails using Microsoft Graph API',
    'description': """
Microsoft Graph API Mail Gateway
===============================

This module allows Odoo to send emails using Microsoft Graph API instead of SMTP.
It provides OAuth authentication with Microsoft and handles token refresh.
    """,
    'author': 'Odoo',
    'website': 'https://www.odoo.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/mail_server_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
} 