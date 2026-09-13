# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        subscription = self.env["saas.subscription"].sudo().search([], limit=1)
        if subscription:
            for vals in vals_list:
                if vals.get("active", True):
                    subscription.check_limit("users")
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("active") is True:
            subscription = self.env["saas.subscription"].sudo().search([], limit=1)
            if subscription:
                for user in self:
                    if not user.active:
                        subscription.check_limit("users")
        return super().write(vals)
