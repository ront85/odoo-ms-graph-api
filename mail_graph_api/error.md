Log:
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,155 13110 INFO lynxgrp werkzeug: 81.221.207.148 - - [04/Apr/2025 21:03:14] "POST /web/action/load HTTP/1.0" 200 - 10 0.006 0.014
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,306 13110 DEBUG lynxgrp odoo.api: call mail.mail().get_views(options={'action_id': 118, 'embedded_action_id': False, 'embedded_parent_res_id': False, 'load_filters': True, 'toolbar': True}, views=[[False, 'list'], [False, 'form'], [330, 'search']])
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,395 13110 INFO lynxgrp werkzeug: 81.221.207.148 - - [04/Apr/2025 21:03:14] "POST /web/dataset/call_kw/mail.mail/get_views HTTP/1.0" 200 - 52 0.029 0.063
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,457 13110 DEBUG lynxgrp odoo.api: call mail.mail().web_search_read(count_limit=10001, domain=[], limit=80, offset=0, order='', specification={'date': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'recipient_ids': {}, 'model': {}, 'res_id': {}, 'email_from': {}, 'message_type': {}, 'state': {}})
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,475 13110 INFO lynxgrp werkzeug: 81.221.207.148 - - [04/Apr/2025 21:03:14] "POST /web/dataset/call_kw/mail.mail/web_search_read HTTP/1.0" 200 - 7 0.008 0.027
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,481 13110 DEBUG lynxgrp odoo.api: call res.users(6,).has_group('base.group_allow_export')
Apr 04 21:03:14 cloud python3[13110]: 2025-04-04 21:03:14,482 13110 INFO lynxgrp werkzeug: 81.221.207.148 - - [04/Apr/2025 21:03:14] "POST /web/dataset/call_kw/res.users/has_group HTTP/1.0" 200 - 1 0.001 0.004
Apr 04 21:03:16 cloud python3[13110]: 2025-04-04 21:03:16,058 13110 DEBUG lynxgrp odoo.api: call mail.mail(61,).web_read(specification={'message_type': {}, 'state': {}, 'model': {}, 'res_id': {'fields': {'display_name': {}}}, 'mail_message_id_int': {}, 'subject': {}, 'author_id': {'fields': {'display_name': {}}}, 'date': {}, 'email_from': {}, 'email_to': {}, 'recipient_ids': {'fields': {'display_name': {}}, 'context': {'active_test': False}}, 'email_cc': {}, 'reply_to': {}, 'scheduled_date': {}, 'body_content': {}, 'body_html': {}, 'auto_delete': {}, 'is_notification': {}, 'mail_server_id': {'fields': {'display_name': {}}}, 'message_id': {}, 'references': {}, 'fetchmail_server_id': {'fields': {'display_name': {}}}, 'headers': {}, 'restricted_attachment_count': {}, 'unrestricted_attachment_ids': {'fields': {'name': {}, 'website_id': {'fields': {'display_name': {}}}, 'res_model': {}, 'res_field': {}, 'res_id': {'fields': {'display_name': {}}}, 'type': {}, 'file_size': {}, 'company_id': {'fields': {'display_name': {}}}, 'create_uid': {'fields': {'display_name': {}}}, 'create_date': {}}, 'limit': 40, 'order': ''}, 'failure_reason': {}, 'display_name': {}})
Apr 04 21:03:16 cloud python3[13110]: 2025-04-04 21:03:16,074 13110 INFO lynxgrp werkzeug: 81.221.207.148 - - [04/Apr/2025 21:03:16] "POST /web/dataset/call_kw/mail.mail/web_read HTTP/1.0" 200 - 7 0.006 0.015
Apr 04 21:03:17 cloud python3[13110]: 2025-04-04 21:03:17,141 13110 DEBUG lynxgrp odoo.api: call mail.mail(61,).send()
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,470 13113 DEBUG ? odoo.service.server: WorkerCron (13113) polling for jobs
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,518 13113 INFO ? odoo.sql_db: ConnectionPool(read/write;used=1/count=1/max=64): Closed 1 connections to 'user=odoo password=xxx dbname=lynxgrp-accounting host=localhost port=5432 application_name=odoo-13113 sslmode=disable'
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,520 13113 DEBUG ? odoo.service.server: WorkerCron (13113) polling for jobs
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,561 13113 INFO ? odoo.sql_db: ConnectionPool(read/write;used=1/count=1/max=64): Closed 1 connections to 'user=odoo password=xxx dbname=lynxgrp-plm host=localhost port=5432 application_name=odoo-13113 sslmode=disable'
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,565 13113 DEBUG ? odoo.service.server: WorkerCron (13113) polling for jobs
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,607 13113 INFO ? odoo.sql_db: ConnectionPool(read/write;used=1/count=1/max=64): Closed 1 connections to 'user=odoo password=xxx dbname=lynxgrp-sandbox host=localhost port=5432 application_name=odoo-13113 sslmode=disable'
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,611 13113 DEBUG ? odoo.service.server: WorkerCron (13113) polling for jobs
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,656 13113 WARNING odoo18 odoo.addons.base.models.ir_cron: Skipping database odoo18 because of modules to install/upgrade/remove.
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,658 13113 INFO ? odoo.sql_db: ConnectionPool(read/write;used=1/count=1/max=64): Closed 1 connections to 'user=odoo password=xxx dbname=odoo18 host=localhost port=5432 application_name=odoo-13113 sslmode=disable'
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,660 13113 DEBUG ? odoo.service.server: WorkerCron (13113) polling for jobs
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,701 13113 INFO ? odoo.sql_db: ConnectionPool(read/write;used=1/count=1/max=64): Closed 1 connections to 'user=odoo password=xxx dbname=your_db_name host=localhost port=5432 application_name=odoo-13113 sslmode=disable'
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,705 13113 DEBUG ? odoo.service.server: WorkerCron (13113) polling for jobs
Apr 04 21:03:53 cloud python3[13113]: 2025-04-04 21:03:53,750 13113 INFO ? odoo.sql_db: ConnectionPool(read/write;used=1/count=1/max=64): Closed 1 connections to 'user=odoo password=xxx dbname=lynxgrp host=localhost port=5432 application_name=odoo-13113 sslmode=disable'


Odoo shell:
odoo@cloud:/opt/odoo18/custom_addons/mail_graph_api$ /opt/odoo18/odoo-bin shell -d lynxgrp
2025-04-04 21:12:07,090 13386 INFO ? odoo: Odoo version 18.0
2025-04-04 21:12:07,091 13386 INFO ? odoo: addons paths: ['/opt/odoo18/odoo/addons', '/usr/lib/python3/dist-packages/odoo/addons', '/var/lib/odoo/.local/share/Odoo/addons/18.0', '/opt/odoo18/addons']
2025-04-04 21:12:07,091 13386 INFO ? odoo: database: default@default:default
Warn: Can't find .pfb for face 'Courier'
2025-04-04 21:12:07,420 13386 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltopdf binary at /usr/local/bin/wkhtmltopdf
2025-04-04 21:12:07,434 13386 INFO ? odoo.addons.base.models.ir_actions_report: Will use the Wkhtmltoimage binary at /usr/local/bin/wkhtmltoimage
2025-04-04 21:12:07,682 13386 INFO ? odoo.service.server: Initiating shutdown
2025-04-04 21:12:07,682 13386 INFO ? odoo.service.server: Hit CTRL-C again or send a second signal to force the shutdown.
2025-04-04 21:12:07,694 13386 INFO lynxgrp odoo.modules.loading: loading 1 modules...
2025-04-04 21:12:07,703 13386 INFO lynxgrp odoo.modules.loading: 1 modules loaded in 0.01s, 0 queries (+0 extra)
2025-04-04 21:12:07,715 13386 WARNING lynxgrp odoo.modules.graph: module report_xlsx: not installable, skipped
2025-04-04 21:12:07,756 13386 WARNING lynxgrp odoo.modules.graph: module mail_graph_api: not installable, skipped
2025-04-04 21:12:07,765 13386 WARNING lynxgrp odoo.modules.graph: module purchase_bom_summary: not installable, skipped
2025-04-04 21:12:07,824 13386 INFO lynxgrp odoo.modules.loading: loading 242 modules...
2025-04-04 21:12:07,831 13386 WARNING lynxgrp odoo.addons.attachment_indexation.models.ir_attachment: Attachment indexation of PDF documents is unavailable because the 'pdfminer' Python library cannot be found on the system. You may install it from https://pypi.org/project/pdfminer.six/ (e.g. `pip3 install pdfminer.six`)
2025-04-04 21:12:09,900 13386 INFO lynxgrp odoo.modules.loading: 242 modules loaded in 2.08s, 0 queries (+0 extra)
2025-04-04 21:12:10,640 13386 ERROR lynxgrp odoo.modules.loading: Some modules are not loaded, some dependencies or manifest may be missing: ['mail_graph_api', 'purchase_bom_summary', 'report_xlsx']
2025-04-04 21:12:10,642 13386 INFO lynxgrp odoo.modules.loading: Modules loaded.
2025-04-04 21:12:10,656 13386 INFO lynxgrp odoo.modules.registry: Registry loaded in 2.973s
env: <odoo.api.Environment object at 0x7e226c1023c0>
odoo: <module 'odoo' from '/opt/odoo18/odoo/__init__.py'>
openerp: <module 'odoo' from '/opt/odoo18/odoo/__init__.py'>
self: res.users(1,)
Python 3.12.3 (main, Feb  4 2025, 14:48:35) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(Console)
>>>
