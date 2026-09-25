import re

DEFAULT_BRAND_LOGO = "/cashbook/static/img/brand_logo.png"

# auth_signup invite templates (mail.template records, not QWeb views)
_POWERED_BY_BLOCK = re.compile(
    r"<!--\s*POWERED BY\s*-->.*?</tr>\s*",
    re.DOTALL | re.IGNORECASE,
)


def _strip_odoo_email_footer(env):
    Template = env["mail.template"].sudo()
    for template in Template.search([("body_html", "ilike", "Powered by%Odoo%")]):
        body = template.body_html or ""
        cleaned = _POWERED_BY_BLOCK.sub("", body)
        if cleaned != body:
            template.body_html = cleaned


def post_init_hook(env):
    env["cashbook.partner"]._migrate_legacy_types()
    env["cashbook.business"]._ensure_cashbook_currencies()
    icp = env["ir.config_parameter"].sudo()
    logo = icp.get_param("cashbook.brand_logo") or ""
    if not logo or logo.endswith(".svg"):
        icp.set_param("cashbook.brand_logo", DEFAULT_BRAND_LOGO)
    _strip_odoo_email_footer(env)
