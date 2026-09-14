# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

from odoo import Command, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _saas_platform_groups(self):
        return {
            "it_support": self.env.ref(
                "softobro_saas_subscription.group_it_support", raise_if_not_found=False
            ),
            "subscriber_admin": self.env.ref(
                "softobro_saas_subscription.group_subscriber_admin",
                raise_if_not_found=False,
            ),
            "system": self.env.ref("base.group_system"),
            "erp_manager": self.env.ref("base.group_erp_manager"),
        }

    @api.model
    def _saas_apply_subscriber_lockdown_all(self):
        if not self.env["saas.platform.mixin"].saas_tenant_mode():
            return
        self.search([("share", "=", False)])._saas_apply_subscriber_lockdown()

    def _saas_apply_subscriber_lockdown(self):
        if not self.env["saas.platform.mixin"].saas_tenant_mode():
            return
        groups = self._saas_platform_groups()
        it_support = groups["it_support"]
        subscriber_admin = groups["subscriber_admin"]
        blocked = groups["system"] | groups["erp_manager"]
        for user in self:
            if it_support and it_support in user.group_ids:
                continue
            ops = []
            for group in blocked & user.group_ids:
                ops.append(Command.unlink(group.id))
            if subscriber_admin and subscriber_admin not in user.group_ids:
                ops.append(Command.link(subscriber_admin.id))
            if ops:
                user.sudo().write({"group_ids": ops})

    @api.model_create_multi
    def create(self, vals_list):
        subscription = self.env["saas.subscription"].sudo().search([], limit=1)
        if subscription:
            for vals in vals_list:
                if vals.get("active", True):
                    subscription.check_limit("users")
        users = super().create(vals_list)
        users._saas_apply_subscriber_lockdown()
        return users

    def write(self, vals):
        if vals.get("active") is True:
            subscription = self.env["saas.subscription"].sudo().search([], limit=1)
            if subscription:
                for user in self:
                    if not user.active:
                        subscription.check_limit("users")
        res = super().write(vals)
        if "group_ids" in vals or "role" in vals or vals.get("active") is True:
            self._saas_apply_subscriber_lockdown()
        return res
