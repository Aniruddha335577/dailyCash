from odoo import models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _load_menus_blacklist(self):
        res = super()._load_menus_blacklist()
        if not self.env["saas.platform.mixin"].saas_platform_locked():
            return res
        for xmlid in self.env["saas.platform.mixin"].saas_blocked_menu_xmlids():
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                res.append(menu.id)
        return res
