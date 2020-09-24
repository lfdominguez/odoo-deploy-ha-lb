
from .models.ir_attachment_lobject import monkey_patch_ir_attachment
import logging

log = logging.getLogger(__name__)


def setup():
    # Override IrAttachment model to support PostgreSQL Large Objects
    # then ir.config_parameter.xml is loaded to set default storage
    # to 'dblo' (PostgreSQL Large Object)

    log.info("Using Database attachment storage.")
    monkey_patch_ir_attachment()
