from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        if info.get("uid"):
            mixin = self.env["saas.platform.mixin"]
            info["saas_platform_locked"] = mixin.saas_platform_locked()
            info["saas_blocked_paths"] = list(mixin.saas_blocked_paths())
            info["saas_home_url"] = mixin.saas_subscriber_home_url()
        return info
