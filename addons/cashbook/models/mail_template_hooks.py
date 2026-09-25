from odoo import api, models


class CashbookMailTemplateHooks(models.AbstractModel):
    _name = "cashbook.mail_template_hooks"
    _description = "Apply HisabBro mail template overrides"

    @api.model
    def apply_invite_templates(self):
        from odoo.addons.cashbook.hooks import apply_hishabbro_invite_mail_templates

        apply_hishabbro_invite_mail_templates(self.env)
