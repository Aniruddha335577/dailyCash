from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["saas.subscription"].sudo()._ensure_saas_url_config()
    env["saas.subscription"].sudo()._ensure_tenant_public_url()
