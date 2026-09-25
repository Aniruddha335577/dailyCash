from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.cashbook.hooks import apply_hishabbro_invite_mail_templates

    apply_hishabbro_invite_mail_templates(env)
    for xid in (
        "cashbook.cashbook_mail_notification_layout",
        "cashbook.cashbook_mail_notification_light",
    ):
        view = env.ref(xid, raise_if_not_found=False)
        if view:
            view.unlink()
