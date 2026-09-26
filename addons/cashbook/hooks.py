import re

DEFAULT_BRAND_LOGO = "/cashbook/static/img/brand_logo.png"
DEFAULT_OUTBOUND_EMAIL = "noreply@softobro.com"

_POWERED_BY_BLOCK = re.compile(
    r"<!--\s*POWERED BY\s*-->.*?</tr>\s*",
    re.DOTALL | re.IGNORECASE,
)

_INVITE_BODY = """
<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle">
                    <span style="font-size: 10px;">Your workspace</span><br/>
                    <span style="font-size: 20px; font-weight: bold;">
                        <t t-out="object.name or ''">User</t>
                    </span>
                </td><td valign="middle" align="right" t-if="not object.company_id.uses_default_logo">
                    <img t-attf-src="/logo.png?company={{ object.company_id.id }}" style="padding: 0px; margin: 0px; height: auto; width: 80px;" t-att-alt="object.company_id.name"/>
                </td></tr>
                <tr><td colspan="2" style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Dear <t t-out="object.name or ''">User</t>,<br /><br />
                        You have been invited to <strong><t t-out="object.env['ir.config_parameter'].sudo().get_param('cashbook.brand_name', 'HisabBro')"/></strong>.
                        <div style="margin: 16px 0px 16px 0px;">
                            <a t-att-href="object.partner_id._get_signup_url()"
                                t-attf-style="background-color: {{object.company_id.email_secondary_color or '#875A7B'}}; padding: 8px 16px 8px 16px; text-decoration: none; color: {{object.company_id.email_primary_color or '#FFFFFF'}}; border-radius: 5px; font-size:13px;">
                                Accept invitation
                            </a>
                        </div>
                        <b>This link will remain valid for
                        <t t-out="int(int(object.env['ir.config_parameter'].sudo().get_param('auth_signup.signup.validity.hours',144))/24)"></t> days.</b><br/>
                        <t t-set="website_url" t-value="object.env['ir.config_parameter'].sudo().get_param('saas.tenant.public_url') or object.get_base_url()"></t>
                        Your workspace URL: <b><a t-att-href="website_url" t-out="website_url or ''">https://example.com</a></b><br/>
                        Sign in email: <b><t t-out="object.email or ''">user@example.com</t></b><br/><br/>
                        If you did not expect this invitation, you can ignore this email.
                        <br/><br/>
                        Thanks,<br/>HishabBro
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="object.company_id.name or ''">Company</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-if="object.company_id.email">
                        <a t-att-href="'mailto:%s' % object.company_id.email" style="text-decoration:none; color: #454748;" t-out="object.company_id.email or ''">noreply@softobro.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
</table>
"""


def apply_hishabbro_invite_mail_templates(env):
    icp = env["ir.config_parameter"].sudo()
    brand = icp.get_param("cashbook.brand_name") or "HisabBro"
    subject_internal = f"You are invited to {brand}"
    subject_portal = f"Your {brand} account"

    email_from = f'"{brand}" <{DEFAULT_OUTBOUND_EMAIL}>'
    updates = {
        "auth_signup.set_password_email": {
            "subject": subject_internal,
            "email_from": email_from,
            "body_html": _INVITE_BODY,
        },
        "auth_signup.portal_set_password_email": {
            "subject": subject_portal,
            "email_from": email_from,
            "body_html": _INVITE_BODY.replace(
                "Accept invitation", "Activate account"
            ),
        },
    }
    for xmlid, vals in updates.items():
        template = env.ref(xmlid, raise_if_not_found=False)
        if template:
            template.write(vals)


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
    apply_hishabbro_invite_mail_templates(env)
    _strip_odoo_email_footer(env)
