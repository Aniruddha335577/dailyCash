from odoo import api, models

SAAS_BLOCKED_MENU_XMLIDS = (
    "base.menu_management",
    "base.menu_administration",
    "base.menu_tests",
    "mail.menu_root_discuss",
)

SAAS_BLOCKED_PATHS = (
    "apps",
    "settings",
    "discuss",
)

SAAS_BLOCKED_ACTION_FRAGMENTS = (
    "open_module_tree",
    "action_general_configuration",
    "action_discuss",
    "mail.action_discuss",
)


class SaasPlatformMixin(models.AbstractModel):
    _name = "saas.platform.mixin"
    _description = "SaaS platform helpers"

    @api.model
    def saas_tenant_mode(self):
        return (
            self.env["ir.config_parameter"].sudo().get_param("saas.tenant_mode", "True")
            == "True"
        )

    @api.model
    def is_it_support_user(self, user=None):
        user = user or self.env.user
        return user.has_group("softobro_saas_subscription.group_it_support")

    @api.model
    def saas_platform_locked(self, user=None):
        """True when the user must not access Odoo platform apps."""
        user = user or self.env.user
        if not self.saas_tenant_mode():
            return False
        return not self.is_it_support_user(user)

    @api.model
    def saas_blocked_menu_xmlids(self):
        return SAAS_BLOCKED_MENU_XMLIDS

    @api.model
    def saas_blocked_paths(self):
        return SAAS_BLOCKED_PATHS

    @api.model
    def saas_path_blocked(self, subpath):
        if not subpath:
            return False
        first = subpath.strip("/").split("/")[0]
        if first in SAAS_BLOCKED_PATHS:
            return True
        if first.startswith("action-"):
            return any(token in first for token in SAAS_BLOCKED_ACTION_FRAGMENTS)
        return False

    @api.model
    def saas_action_blocked(self, action_name):
        if not action_name:
            return False
        action_name = str(action_name)
        if action_name in SAAS_BLOCKED_PATHS:
            return True
        return any(fragment in action_name for fragment in SAAS_BLOCKED_ACTION_FRAGMENTS)

    @api.model
    def saas_subscriber_home_url(self):
        menu = self.env.ref("cashbook.menu_cashbook_root", raise_if_not_found=False)
        if menu:
            return f"/odoo?menu_id={menu.id}"
        return "/odoo"
