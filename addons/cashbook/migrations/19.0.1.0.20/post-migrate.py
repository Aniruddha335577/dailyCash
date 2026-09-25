from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.cashbook.hooks import _strip_odoo_email_footer

    _strip_odoo_email_footer(env)
