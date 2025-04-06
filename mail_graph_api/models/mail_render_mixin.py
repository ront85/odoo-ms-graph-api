# -*- coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)

class MailRenderMixin(models.AbstractModel):
    _inherit = 'mail.render.mixin'
    
    def _render_template(self, template_src, model, res_ids, **kwargs):
        """Override to handle engine parameter compatibility with Odoo versions"""
        _logger.info("MAIL_GRAPH_API: Patched _render_template called with kwargs: %s", kwargs)
        
        # Remove engine parameter if exists and pass the rest of the kwargs
        if 'engine' in kwargs:
            _logger.info("MAIL_GRAPH_API: Removing engine parameter for compatibility")
            engine = kwargs.pop('engine')
            _logger.info("MAIL_GRAPH_API: Using engine: %s", engine)
        
        # Call the original method with compatible parameters
        return super(MailRenderMixin, self)._render_template(template_src, model, res_ids, **kwargs) 