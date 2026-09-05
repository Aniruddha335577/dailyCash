from . import models

from odoo.tools import config

if config.get("test_enable"):
    from . import tests  # noqa: F401
