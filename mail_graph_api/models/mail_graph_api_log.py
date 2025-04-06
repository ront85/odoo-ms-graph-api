# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MailGraphApiLog(models.Model):
    _name = 'mail.graph.api.log'
    _description = 'Microsoft Graph API Log'
    _order = 'create_date desc'
    
    server_id = fields.Many2one('ir.mail_server', string='Mail Server')
    level = fields.Selection([
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error')
    ], string='Level', default='INFO')
    message = fields.Text(string='Message')
    
    @api.model
    def add_log(self, server_id, message, level='INFO'):
        """Add a new log entry"""
        return self.create({
            'server_id': server_id,
            'message': message,
            'level': level
        })
    
    @api.model
    def clear_logs(self, server_id=None):
        """Clear logs for a specific server or all logs if no server_id"""
        domain = [('server_id', '=', server_id)] if server_id else []
        return self.search(domain).unlink() 