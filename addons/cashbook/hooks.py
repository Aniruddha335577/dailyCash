DEFAULT_BRAND_LOGO = "/cashbook/static/img/brand_logo.png"


def post_init_hook(env):
    env["cashbook.partner"]._migrate_legacy_types()
    env["cashbook.business"]._ensure_cashbook_currencies()
    icp = env["ir.config_parameter"].sudo()
    logo = icp.get_param("cashbook.brand_logo") or ""
    if not logo or logo.endswith(".svg"):
        icp.set_param("cashbook.brand_logo", DEFAULT_BRAND_LOGO)
