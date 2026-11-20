from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    icp = env["ir.config_parameter"].sudo()
    defaults = {
        "saas.public_base_domain": "softobro.com",
        "saas.tenant_url_suffix": "-dailycash",
        "saas.public_url_scheme": "https",
    }
    for key, value in defaults.items():
        if not icp.get_param(key):
            icp.set_param(key, value)
    env["saas.subscription"].sudo()._ensure_tenant_public_url()
