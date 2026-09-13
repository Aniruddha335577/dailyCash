import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_COLOR_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


class CashbookReportTemplate(models.Model):
    _name = "cashbook.report.template"
    _description = "CashBook Report Template"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(string="Default Template", default=False)

    # Branding visibility (data comes from cashbook.business at render time)
    show_saas_logo = fields.Boolean(string="SaaS Logo", default=True)
    show_powered_by = fields.Boolean(string="Powered By Line", default=True)
    show_footer_contact = fields.Boolean(string="Footer Contact", default=True)
    show_logo = fields.Boolean(default=True)
    show_company_name = fields.Boolean(default=True)
    show_legal_name = fields.Boolean(default=True)
    show_address = fields.Boolean(default=True)
    show_phone = fields.Boolean(default=True)
    show_email = fields.Boolean(default=True)
    show_website = fields.Boolean(default=False)
    show_tax_id = fields.Boolean(default=False)

    # Header
    header_text = fields.Text(string="Header Text")
    header_alignment = fields.Selection(
        selection=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
        ],
        default="left",
        required=True,
    )

    # Entry information visibility
    show_invoice_number = fields.Boolean(string="Invoice Number", default=True)
    show_entry_number = fields.Boolean(string="Entry Number", default=False)
    show_date = fields.Boolean(default=True)
    show_partner = fields.Boolean(default=True)
    show_book = fields.Boolean(string="Book", default=True)
    show_entry_type = fields.Boolean(string="Entry Type", default=True)
    show_reference = fields.Boolean(string="Reference", default=True)
    show_description = fields.Boolean(string="Description", default=True)
    show_payment_method = fields.Boolean(default=True)
    show_money_direction = fields.Boolean(default=True)
    show_line_items = fields.Boolean(string="Line Items", default=True)
    show_amount = fields.Boolean(default=True)
    show_paid = fields.Boolean(string="Paid Amount", default=True)
    show_due = fields.Boolean(string="Due Amount", default=True)

    # Footer
    footer_text = fields.Text(
        string="Footer Text",
        help="Optional override. Leave empty to use the business invoice footer.",
    )
    footer_alignment = fields.Selection(
        selection=[
            ("left", "Left"),
            ("center", "Center"),
            ("right", "Right"),
        ],
        default="center",
        required=True,
    )
    show_page_number = fields.Boolean(default=True)

    # Appearance
    primary_color = fields.Char(default="#2563eb")
    page_size = fields.Selection(
        selection=[
            ("a4", "A4"),
            ("a5", "A5"),
        ],
        default="a4",
        required=True,
    )
    margin_top = fields.Integer(default=20)
    margin_bottom = fields.Integer(default=20)
    margin_left = fields.Integer(default=15)
    margin_right = fields.Integer(default=15)

    layout = fields.Selection(
        selection=[
            ("simple", "Simple"),
            ("classic", "Classic"),
            ("modern", "Modern"),
        ],
        default="classic",
        required=True,
    )

    @api.model
    def _get_default_template(self):
        template = self.search(
            [("is_default", "=", True), ("active", "=", True)],
            limit=1,
        )
        if not template:
            template = self.search([("active", "=", True)], limit=1)
        return template

    @api.constrains("is_default")
    def _check_single_default(self):
        for template in self.filtered("is_default"):
            others = self.search([
                ("is_default", "=", True),
                ("id", "!=", template.id),
                ("active", "=", True),
            ])
            if others:
                raise ValidationError(
                    _("Only one active report template can be marked as default.")
                )

    @api.constrains("primary_color")
    def _check_primary_color(self):
        for template in self:
            if template.primary_color and not _COLOR_RE.match(template.primary_color):
                raise ValidationError(
                    _("Primary color must be a valid hex value, e.g. #2563eb.")
                )

    @api.constrains("margin_top", "margin_bottom", "margin_left", "margin_right")
    def _check_margins(self):
        for template in self:
            for field_name in ("margin_top", "margin_bottom", "margin_left", "margin_right"):
                value = template[field_name]
                if value < 5 or value > 50:
                    raise ValidationError(
                        _("Page margins must be between 5 and 50 mm.")
                    )

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault("name", _("%s (copy)", self.name))
        default["is_default"] = False
        return super().copy(default)

    def action_preview(self):
        self.ensure_one()
        entry = self.env["cashbook.entry"].search([], limit=1, order="id desc")
        if not entry:
            raise UserError(
                _("Create at least one CashBook entry before previewing a report template.")
            )
        return self.env.ref("cashbook.action_report_cashbook_entry").report_action(
            entry.with_context(force_report_template_id=self.id)
        )
