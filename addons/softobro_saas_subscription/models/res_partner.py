# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_base_url(self) -> str:
        self.ensure_one()
        if self.env["saas.platform.mixin"].saas_tenant_mode():
            resolved = self.env["saas.subscription"].sudo()._resolve_public_base_url()
            if resolved:
                return resolved
        return super().get_base_url()
