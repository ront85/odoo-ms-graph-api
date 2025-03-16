# Microsoft Graph API Mail Gateway for Odoo

This module allows Odoo to send emails using Microsoft Graph API instead of SMTP.

## Features

- Send emails using Microsoft Graph API
- OAuth2 authentication with Microsoft
- Automatic token refresh
- Support for attachments
- Detailed logging for debugging

## Installation

1. Copy the `mail_graph_api` folder to your Odoo addons directory
2. Restart Odoo server
3. Go to Apps and install the "Microsoft Graph API Mail Gateway" module

## Configuration

### Azure Application Setup

1. Go to the [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations" and create a new application
3. Set the following redirect URI: `https://your-odoo-domain.com/mail_graph_api/auth/callback`
4. Under "API permissions", add the following delegated permissions:
   - `Mail.Send`
5. Grant admin consent for these permissions
6. Under "Certificates & secrets", create a new client secret and note it down

### Odoo Configuration

1. Go to Settings > Technical > Email > Outgoing Mail Servers
2. Create a new mail server or edit an existing one
3. Enable "Use Microsoft Graph API"
4. Fill in the following fields:
   - Client ID: Your Azure application client ID
   - Client Secret: Your Azure application client secret
   - Tenant ID: Your Azure tenant ID (found in Azure Portal)
   - Sender Email: The email address to send from

5. Click "Authenticate with Microsoft" and follow the prompts
6. After successful authentication, click "Test Connection" to verify everything works

## Troubleshooting

If you encounter issues:

1. Check the "Graph API Logs" tab in the mail server form
2. Ensure your Azure application has the correct permissions
3. Verify that admin consent has been granted for the permissions
4. Check that the redirect URI is correctly configured in Azure

## Support

For issues or feature requests, please contact your Odoo support provider. 