from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.cashbook.hooks import apply_dailycash_invite_mail_templates

    apply_dailycash_invite_mail_templates(env)
