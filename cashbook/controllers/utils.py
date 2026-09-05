from odoo.http import request
from odoo.tools import config


def cashbook_saas_mode():
    """Return True when CashBook should behave as a SaaS tenant (hide DB manager UI)."""
    conf_val = config.get("cashbook_saas_mode")
    if conf_val is not None:
        return str(conf_val).lower() in ("1", "true", "yes")
    if request.db:
        return (
            request.env["ir.config_parameter"].sudo().get_param("cashbook.saas_mode", "True")
            == "True"
        )
    return True
