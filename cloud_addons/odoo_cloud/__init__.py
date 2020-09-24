
from . import models
from . import redis_session_store
from . import attachment_storage

# Apply Odoo Server Patches
redis_session_store.setup()
attachment_storage.setup()
