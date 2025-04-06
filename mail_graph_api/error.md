06 14:11:38 cloud python3[95544]: 2025-04-06 14:11:38,733 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:11:38] "POST /web/dataset/call_kw/ir.mail_server/web_read HTTP/1.0" 200 - 4 0.002 0.014
Apr 06 14:11:41 cloud python3[95545]: 2025-04-06 14:11:41,471 95545 DEBUG lynxgrp odoo.api: call ir.mail_server(5,).test_send_email()
Apr 06 14:11:41 cloud python3[95545]: 2025-04-06 14:11:41,479 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.mail_server: GRAPH API (Microsoft 365 Email): Sending test email to ron.tiso@lynxgroup.ch
Apr 06 14:11:41 cloud python3[95545]: 2025-04-06 14:11:41,870 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.mail_server: GRAPH API (Microsoft 365 Email): Test email sent successfully
Apr 06 14:11:41 cloud python3[95545]: 2025-04-06 14:11:41,878 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:11:41] "POST /web/dataset/call_button/ir.mail_server/test_send_email HTTP/1.0" 200 - 7 0.007 0.405
Apr 06 14:11:47 cloud python3[95544]: 2025-04-06 14:11:47,889 95544 DEBUG lynxgrp odoo.api: call ir.mail_server(5,).run_graph_api_diagnostics()
Apr 06 14:11:47 cloud python3[95544]: 2025-04-06 14:11:47,891 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.mail_server: GRAPH API (Microsoft 365 Email): Running Graph API diagnostics
Apr 06 14:11:48 cloud python3[95544]: 2025-04-06 14:11:48,034 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.mail_server: GRAPH API (Microsoft 365 Email): API connection successful, connected as: Ron Tiso
Apr 06 14:11:48 cloud python3[95544]: 2025-04-06 14:11:48,043 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:11:48] "POST /web/dataset/call_button/ir.mail_server/run_graph_api_diagnostics HTTP/1.0" 200 - 6 0.005 0.154
Apr 06 14:11:53 cloud python3[95544]: 2025-04-06 14:11:53,669 95544 DEBUG lynxgrp odoo.api: call ir.mail_server(5,).action_view_debug_logs()
Apr 06 14:11:53 cloud python3[95544]: 2025-04-06 14:11:53,670 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:11:53] "POST /web/dataset/call_button/ir.mail_server/action_view_debug_logs HTTP/1.0" 200 - 1 0.001 0.004
Apr 06 14:11:53 cloud python3[95544]: 2025-04-06 14:11:53,913 95544 DEBUG lynxgrp odoo.api: call ir.mail_server(5,).web_read(specification={'name': {}, 'from_filter': {}, 'sequence': {}, 'max_email_size': {}, 'use_graph_api': {}, 'smtp_authentication': {}, 'smtp_authentication_info': {}, 'smtp_encryption': {}, 'smtp_debug': {}, 'smtp_host': {}, 'smtp_port': {}, 'smtp_user': {}, 'smtp_pass': {}, 'smtp_ssl_certificate': {}, 'smtp_ssl_private_key': {}, 'ms_client_id': {}, 'ms_client_secret': {}, 'ms_tenant_id': {}, 'ms_sender_email': {}, 'ms_access_token': {}, 'ms_refresh_token': {}, 'ms_token_expiry': {}, 'debug_mode': {}, 'graph_api_logs': {}, 'active': {}, 'display_name': {}})
Apr 06 14:11:53 cloud python3[95544]: 2025-04-06 14:11:53,932 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:11:53] "POST /web/dataset/call_kw/ir.mail_server/web_read HTTP/1.0" 200 - 4 0.004 0.023
Apr 06 14:11:54 cloud python3[95545]: 2025-04-06 14:11:54,077 95545 ERROR lynxgrp odoo.http: Exception during request handling.
Apr 06 14:11:54 cloud python3[95545]: Traceback (most recent call last):
Apr 06 14:11:54 cloud python3[95545]:   File "<2618>", line 1663, in template_2618
Apr 06 14:11:54 cloud python3[95545]:   File "<2618>", line 1172, in template_2618_content
Apr 06 14:11:54 cloud python3[95545]: KeyError: 'website'
Apr 06 14:11:54 cloud python3[95545]: The above exception was the direct cause of the following exception:
Apr 06 14:11:54 cloud python3[95545]: Traceback (most recent call last):
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 2366, in __call__
Apr 06 14:11:54 cloud python3[95545]:     response = request._serve_db()
Apr 06 14:11:54 cloud python3[95545]:                ^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 1894, in _serve_db
Apr 06 14:11:54 cloud python3[95545]:     return self._transactioning(
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 1957, in _transactioning
Apr 06 14:11:54 cloud python3[95545]:     return service_model.retrying(func, env=self.env)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/service/model.py", line 137, in retrying
Apr 06 14:11:54 cloud python3[95545]:     result = func()
Apr 06 14:11:54 cloud python3[95545]:              ^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 1924, in _serve_ir_http
Apr 06 14:11:54 cloud python3[95545]:     response = self.dispatcher.dispatch(rule.endpoint, args)
Apr 06 14:11:54 cloud python3[95545]:                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 2084, in dispatch
Apr 06 14:11:54 cloud python3[95545]:     return self.request.registry['ir.http']._dispatch(endpoint)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/addons/base/models/ir_http.py", line 331, in _dispatch
Apr 06 14:11:54 cloud python3[95545]:     result.flatten()
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 1388, in flatten
Apr 06 14:11:54 cloud python3[95545]:     self.response.append(self.render())
Apr 06 14:11:54 cloud python3[95545]:                          ^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/http.py", line 1380, in render
Apr 06 14:11:54 cloud python3[95545]:     return request.env["ir.ui.view"]._render_template(self.template, self.qcontext)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/usr/lib/python3/dist-packages/odoo/addons/web_studio/models/ir_ui_view.py", line 1332, in _render_template
Apr 06 14:11:54 cloud python3[95545]:     return super(View, self)._render_template(template, values)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/usr/lib/python3/dist-packages/odoo/addons/website/models/ir_ui_view.py", line 449, in _render_template
Apr 06 14:11:54 cloud python3[95545]:     return super()._render_template(template, values=values)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/addons/base/models/ir_ui_view.py", line 2191, in _render_template
Apr 06 14:11:54 cloud python3[95545]:     return self.env['ir.qweb']._render(template, values)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/tools/profiler.py", line 306, in _tracked_method_render
Apr 06 14:11:54 cloud python3[95545]:     return method_render(self, template, values, **options)
Apr 06 14:11:54 cloud python3[95545]:            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "/opt/odoo18/odoo/addons/base/models/ir_qweb.py", line 601, in _render
Apr 06 14:11:54 cloud python3[95545]:     result = ''.join(rendering)
Apr 06 14:11:54 cloud python3[95545]:              ^^^^^^^^^^^^^^^^^^
Apr 06 14:11:54 cloud python3[95545]:   File "<4247>", line 131, in template_4247
Apr 06 14:11:54 cloud python3[95545]:   File "<4247>", line 120, in template_4247_content
Apr 06 14:11:54 cloud python3[95545]:   File "<184>", line 51, in template_184
Apr 06 14:11:54 cloud python3[95545]:   File "<184>", line 40, in template_184_content
Apr 06 14:11:54 cloud python3[95545]:   File "<2618>", line 1671, in template_2618
Apr 06 14:11:54 cloud python3[95545]: odoo.addons.base.models.ir_qweb.QWebException: Error while render the template
Apr 06 14:11:54 cloud python3[95545]: KeyError: 'website'
Apr 06 14:11:54 cloud python3[95545]: Template: website.layout
Apr 06 14:11:54 cloud python3[95545]: Path: /t/t[2]
Apr 06 14:11:54 cloud python3[95545]: Node: <t t-if="not request.env.user._is_public()" t-set="nothing" t-value="html_data.update({             \'data-is-published\': \'website_published\' in main_object.fields_get() and main_object.website_published,             \'data-can-optimize-seo\': \'website_meta_description\' in main_object.fields_get(),             \'data-can-publish\': \'can_publish\' in main_object.fields_get() and main_object.can_publish,             \'data-editable-in-backend\': edit_in_backend or (\'website_published\' in main_object.fields_get() and main_object._name != \'website.page\'),         })"/>
Apr 06 14:11:54 cloud python3[95545]: 2025-04-06 14:11:54,087 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:11:54] "GET /mail_graph_api/debug HTTP/1.0" 500 - 21 0.030 0.174
Apr 06 14:12:05 cloud python3[95545]: 2025-04-06 14:12:05,054 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:05] "POST /web/action/load HTTP/1.0" 200 - 10 0.005 0.012
Apr 06 14:12:05 cloud python3[95544]: 2025-04-06 14:12:05,101 95544 DEBUG lynxgrp odoo.api: call mail.mail().get_views(options={'action_id': 118, 'embedded_action_id': False, 'embedded_parent_res_id': False, 'load_filters': True, 'toolbar': True}, views=[[False, 'list'], [False, 'form'], [330, 'search']])
Apr 06 14:12:05 cloud python3[95544]: 2025-04-06 14:12:05,200 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:05] "POST /web/dataset/call_kw/mail.mail/get_views HTTP/1.0" 200 - 49 0.031 0.072
Apr 06 14:12:05 cloud python3[95545]: 2025-04-06 14:12:05,233 95545 DEBUG lynxgrp odoo.api: call mail.mail().web_search_read(count_limit=10001, domain=[], limit=80, offset=0, order='', specification={'date': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'recipient_ids': {}, 'model': {}, 'res_id': {}, 'email_from': {}, 'message_type': {}, 'state': {}})
Apr 06 14:12:05 cloud python3[95545]: 2025-04-06 14:12:05,260 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:05] "POST /web/dataset/call_kw/mail.mail/web_search_read HTTP/1.0" 200 - 16 0.012 0.019
Apr 06 14:12:06 cloud python3[95544]: 2025-04-06 14:12:06,620 95544 DEBUG lynxgrp odoo.api: call mail.mail(61,).web_read(specification={'message_type': {}, 'state': {}, 'model': {}, 'res_id': {'fields': {'display_name': {}}}, 'mail_message_id_int': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'date': {}, 'email_from': {}, 'email_to': {}, 'recipient_ids': {'fields': {'display_name': {}}, 'context': {'active_test': False}}, 'email_cc': {}, 'reply_to': {}, 'scheduled_date': {}, 'body_content': {}, 'body_html': {}, 'auto_delete': {}, 'is_notification': {}, 'mail_server_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'references': {}, 'fetchmail_server_id': {'fields': {'display_name': {}}}, 'headers': {}, 'restricted_attachment_count': {}, 'unrestricted_attachment_ids': {'fields': {'name': {}, 'website_id': {'fields': {'display_name': {}}}, 'res_model': {}, 'res_field': {}, 'res_id': {'fields': {'display_name': {}}}, 'type': {}, 'file_size': {}, 'company_id': {'fields': {'display_name': {}}}, 'create_uid': {'fields': {'display_name': {}}}, 'create_date': {}}, 'limit': 40, 'order': ''}, 'failure_reason': {}, 'display_name': {}})
Apr 06 14:12:06 cloud python3[95544]: 2025-04-06 14:12:06,647 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:06] "POST /web/dataset/call_kw/mail.mail/web_read HTTP/1.0" 200 - 11 0.012 0.019
Apr 06 14:12:09 cloud python3[95545]: 2025-04-06 14:12:09,188 95545 DEBUG lynxgrp odoo.api: call mail.mail(61,).mark_outgoing()
Apr 06 14:12:09 cloud python3[95545]: 2025-04-06 14:12:09,199 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:09] "POST /web/dataset/call_button/mail.mail/mark_outgoing HTTP/1.0" 200 - 6 0.006 0.008
Apr 06 14:12:09 cloud python3[95544]: 2025-04-06 14:12:09,235 95544 DEBUG lynxgrp odoo.api: call mail.mail(61,).web_read(specification={'message_type': {}, 'state': {}, 'model': {}, 'res_id': {'fields': {'display_name': {}}}, 'mail_message_id_int': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'date': {}, 'email_from': {}, 'email_to': {}, 'recipient_ids': {'fields': {'display_name': {}}, 'context': {'active_test': False}}, 'email_cc': {}, 'reply_to': {}, 'scheduled_date': {}, 'body_content': {}, 'body_html': {}, 'auto_delete': {}, 'is_notification': {}, 'mail_server_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'references': {}, 'fetchmail_server_id': {'fields': {'display_name': {}}}, 'headers': {}, 'restricted_attachment_count': {}, 'unrestricted_attachment_ids': {'fields': {'name': {}, 'website_id': {'fields': {'display_name': {}}}, 'res_model': {}, 'res_field': {}, 'res_id': {'fields': {'display_name': {}}}, 'type': {}, 'file_size': {}, 'company_id': {'fields': {'display_name': {}}}, 'create_uid': {'fields': {'display_name': {}}}, 'create_date': {}}, 'limit': 40, 'order': ''}, 'failure_reason': {}, 'display_name': {}})
Apr 06 14:12:09 cloud python3[95544]: 2025-04-06 14:12:09,251 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:09] "POST /web/dataset/call_kw/mail.mail/web_read HTTP/1.0" 200 - 7 0.006 0.015
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,269 95545 DEBUG lynxgrp odoo.api: call mail.mail(61,).send()
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,270 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.debug_patch: === MAIL_DEBUG: send method called for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,271 95545 INFO ? odoo.addons.mail_graph_api.models.debug_patch: === MAIL_DEBUG: Watchdog timer started for send [61] (Thread: 130858654631616) ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,280 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_ir_mail_server: === MAIL_FIX: Using special connect handling for Graph API server Microsoft 365 Email ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,280 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_ir_mail_server: === MAIL_FIX: Returning dummy SMTP connection for Graph API server ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,280 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: _send method called for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,281 95545 INFO ? odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: Watchdog timer started for _send [61] (Thread: 130858654631616) ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,281 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: Using improved Graph API handling for mail IDs [61] ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,281 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_email_bcc: === MAIL_FIX: _send_graph_api_fixed called for mail IDs [61] ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,281 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_email_bcc: === MAIL_FIX: Processing mail ID 61 with Graph API ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,283 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_email_bcc: === MAIL_FIX: Mail ID 61 already attempted with Graph API, skipping ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,283 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: _send method completed for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,283 95545 INFO lynxgrp odoo.addons.mail.models.mail_mail: Sent batch 1 emails via mail server ID #5
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,283 95545 INFO lynxgrp odoo.addons.mail_graph_api.models.debug_patch: === MAIL_DEBUG: send method completed for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:10 cloud python3[95545]: 2025-04-06 14:12:10,285 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:10] "POST /web/dataset/call_button/mail.mail/send HTTP/1.0" 200 - 9 0.004 0.014
Apr 06 14:12:10 cloud python3[95544]: 2025-04-06 14:12:10,315 95544 DEBUG lynxgrp odoo.api: call mail.mail(61,).web_read(specification={'message_type': {}, 'state': {}, 'model': {}, 'res_id': {'fields': {'display_name': {}}}, 'mail_message_id_int': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'date': {}, 'email_from': {}, 'email_to': {}, 'recipient_ids': {'fields': {'display_name': {}}, 'context': {'active_test': False}}, 'email_cc': {}, 'reply_to': {}, 'scheduled_date': {}, 'body_content': {}, 'body_html': {}, 'auto_delete': {}, 'is_notification': {}, 'mail_server_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'references': {}, 'fetchmail_server_id': {'fields': {'display_name': {}}}, 'headers': {}, 'restricted_attachment_count': {}, 'unrestricted_attachment_ids': {'fields': {'name': {}, 'website_id': {'fields': {'display_name': {}}}, 'res_model': {}, 'res_field': {}, 'res_id': {'fields': {'display_name': {}}}, 'type': {}, 'file_size': {}, 'company_id': {'fields': {'display_name': {}}}, 'create_uid': {'fields': {'display_name': {}}}, 'create_date': {}}, 'limit': 40, 'order': ''}, 'failure_reason': {}, 'display_name': {}})
Apr 06 14:12:10 cloud python3[95544]: 2025-04-06 14:12:10,331 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:10] "POST /web/dataset/call_kw/mail.mail/web_read HTTP/1.0" 200 - 7 0.005 0.014
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,344 95544 DEBUG lynxgrp odoo.api: call mail.mail(61,).send()
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,344 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.debug_patch: === MAIL_DEBUG: send method called for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,345 95544 INFO ? odoo.addons.mail_graph_api.models.debug_patch: === MAIL_DEBUG: Watchdog timer started for send [61] (Thread: 130858654631616) ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,355 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_ir_mail_server: === MAIL_FIX: Using special connect handling for Graph API server Microsoft 365 Email ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,355 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_ir_mail_server: === MAIL_FIX: Returning dummy SMTP connection for Graph API server ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,355 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: _send method called for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,356 95544 INFO ? odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: Watchdog timer started for _send [61] (Thread: 130858654631616) ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,356 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: Using improved Graph API handling for mail IDs [61] ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,356 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_email_bcc: === MAIL_FIX: _send_graph_api_fixed called for mail IDs [61] ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,356 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_email_bcc: === MAIL_FIX: Processing mail ID 61 with Graph API ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,358 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_email_bcc: === MAIL_FIX: Mail ID 61 already attempted with Graph API, skipping ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,358 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.fix_freezing_mail: === MAIL_FIX: _send method completed for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,358 95544 INFO lynxgrp odoo.addons.mail.models.mail_mail: Sent batch 1 emails via mail server ID #5
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,358 95544 INFO lynxgrp odoo.addons.mail_graph_api.models.debug_patch: === MAIL_DEBUG: send method completed for mail IDs [61] (Thread: 130858654631616) ===
Apr 06 14:12:16 cloud python3[95544]: 2025-04-06 14:12:16,359 95544 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:16] "POST /web/dataset/call_button/mail.mail/send HTTP/1.0" 200 - 9 0.005 0.015
Apr 06 14:12:16 cloud python3[95545]: 2025-04-06 14:12:16,388 95545 DEBUG lynxgrp odoo.api: call mail.mail(61,).web_read(specification={'message_type': {}, 'state': {}, 'model': {}, 'res_id': {'fields': {'display_name': {}}}, 'mail_message_id_int': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'date': {}, 'email_from': {}, 'email_to': {}, 'recipient_ids': {'fields': {'display_name': {}}, 'context': {'active_test': False}}, 'email_cc': {}, 'reply_to': {}, 'scheduled_date': {}, 'body_content': {}, 'body_html': {}, 'auto_delete': {}, 'is_notification': {}, 'mail_server_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'references': {}, 'fetchmail_server_id': {'fields': {'display_name': {}}}, 'headers': {}, 'restricted_attachment_count': {}, 'unrestricted_attachment_ids': {'fields': {'name': {}, 'website_id': {'fields': {'display_name': {}}}, 'res_model': {}, 'res_field': {}, 'res_id': {'fields': {'display_name': {}}}, 'type': {}, 'file_size': {}, 'company_id': {'fields': {'display_name': {}}}, 'create_uid': {'fields': {'display_name': {}}}, 'create_date': {}}, 'limit': 40, 'order': ''}, 'failure_reason': {}, 'display_name': {}})
Apr 06 14:12:16 cloud python3[95545]: 2025-04-06 14:12:16,404 95545 INFO lynxgrp werkzeug: 81.221.207.148 - - [06/Apr/2025 14:12:16] "POST /web/dataset/call_kw/mail.mail/web_read HTTP/1.0" 200 - 7 0.006 0.014
Apr 06 14:12:24 cloud python3[95537]: 2025-04-06 14:12:24,370 95537 ERROR ? odoo.service.server: WorkerCron (95548) timeout after 120s
Apr 06 14:12:24 cloud python3[95537]: 2025-04-06 14:12:24,397 95537 DEBUG ? odoo.service.server: Worker (95548) unregistered
