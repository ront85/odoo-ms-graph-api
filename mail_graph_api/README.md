# Microsoft Graph API Mail Gateway for Odoo

This module provides seamless integration between Odoo's mail system and Microsoft Graph API, allowing Odoo to send emails using Microsoft 365 accounts instead of traditional SMTP servers.

## Features

- Send emails through Microsoft Graph API instead of SMTP
- OAuth2 authentication with Microsoft Azure
- Automatic token refresh
- Support for email attachments with size limits
- Support for CC and BCC recipients
- Detailed logging for troubleshooting
- Fallback to SMTP option
- Proper timeout handling

## Benefits

- **Enhanced Security**: Uses modern OAuth2 authentication instead of storing SMTP passwords
- **Reliability**: Avoids SMTP blocking and throttling issues
- **Better Deliverability**: Emails are sent directly through Microsoft's infrastructure
- **Simplified Configuration**: No need to configure SMTP ports, encryption, or relay servers

## Requirements

- Odoo 14.0 or newer
- A Microsoft 365 account with appropriate permissions
- An application registered in Azure Active Directory

## Configuration

### Azure Application Setup

1. Go to the [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations" and create a new application
3. Set the redirect URI: `https://your-odoo-domain.com/mail_graph_api/auth/callback`
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

## Technical Implementation

The module integrates with Odoo's email system by:

1. Overriding the `connect()` method in `ir.mail_server` to provide a virtual SMTP connection for Graph API servers
2. Implementing a custom `send_email()` method that uses the Graph API instead of SMTP
3. Handling OAuth2 authentication flow with proper token management
4. Providing automatic token refresh when tokens expire

The implementation follows Odoo best practices and properly integrates with the existing mail system architecture.

## Troubleshooting

If you encounter issues:

1. Check the "Graph API Logs" tab in the mail server form
2. Ensure your Azure application has the correct permissions
3. Verify that admin consent has been granted for the permissions
4. Check that the redirect URI is correctly configured in Azure
5. Verify network connectivity to Microsoft Graph API endpoints

## Support

For issues or feature requests, please contact your Odoo support provider or the module maintainer. 