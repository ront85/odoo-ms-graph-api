from . import mail_server
from . import mail_mail
from . import ir_mail_server
from . import mail_graph_api_log

# Configure logging
import logging
_logger = logging.getLogger(__name__)
_logger.info("=== MAIL_GRAPH_API: Models initialized ===") 