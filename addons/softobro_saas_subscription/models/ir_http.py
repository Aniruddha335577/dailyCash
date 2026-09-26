from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        if info.get("uid"):
            mixin = self.env["saas.platform.mixin"]
            locked = mixin.saas_platform_locked()
            info["saas_platform_locked"] = locked
            info["saas_it_support"] = mixin.is_it_support_user()
            info["saas_blocked_paths"] = list(mixin.saas_blocked_paths())
            info["saas_home_url"] = mixin.saas_subscriber_home_url()
            if locked:
                icp = self.env["ir.config_parameter"].sudo()
                info["support_url"] = icp.get_param("saas.support_url") or False
        return info
