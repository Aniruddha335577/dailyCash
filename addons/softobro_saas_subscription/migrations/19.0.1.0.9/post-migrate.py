def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    env["res.users"]._saas_apply_subscriber_lockdown_all()
