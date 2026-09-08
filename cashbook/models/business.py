import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .saas_restriction import check_business_creation_allowed

_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class CashbookBusiness(models.Model):
    _name = "cashbook.business"
    _description = "CashBook Business"
    _order = "name"

    name = fields.Char(string="Business Name", required=True)
    legal_name = fields.Char(
        string="Legal Name",
        help="Registered legal name if different from the business name shown on documents.",
    )
    logo = fields.Image(
        string="Logo",
        max_width=1024,
        max_height=1024,
    )
    address_line_1 = fields.Char(string="Address Line 1")
    address_line_2 = fields.Char(string="Address Line 2")
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string="State")
    zip = fields.Char(string="ZIP")
    country_id = fields.Many2one("res.country", string="Country")
    phone_1 = fields.Char(string="Phone 1")
    phone_2 = fields.Char(string="Phone 2")
    email = fields.Char(string="Email")
    website = fields.Char(string="Website")
    tax_id = fields.Char(
        string="Tax ID",
        help="VAT, GST, TIN, or other tax registration number printed on invoices.",
    )
    registration_number = fields.Char(
        string="Registration Number",
        help="Business or company registration number.",
    )
    invoice_footer = fields.Text(
        string="Invoice Footer",
        help="Default footer text for invoices, such as payment terms or thank-you note.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    active = fields.Boolean(default=True)
    book_ids = fields.One2many("cashbook.book", "business_id")

    @api.onchange("country_id")
    def _onchange_country_id(self):
        if self.state_id and self.state_id.country_id != self.country_id:
            self.state_id = False

    @api.constrains("email")
    def _check_email(self):
        for business in self.filtered("email"):
            if not _EMAIL_RE.match(business.email.strip()):
                raise ValidationError(_("Enter a valid email address."))

    @api.model_create_multi
    def create(self, vals_list):
        check_business_creation_allowed(self.env, additional=len(vals_list))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("active") is True:
            reactivating = self.filtered(lambda b: not b.active)
            if reactivating:
                check_business_creation_allowed(
                    self.env, additional=len(reactivating)
                )
        return super().write(vals)

    @api.constrains("currency_id")
    def _check_currency(self):
        for business in self:
            if not business.currency_id:
                raise ValidationError(_("Business currency is required."))
