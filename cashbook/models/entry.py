from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CashbookEntry(models.Model):
    _name = "cashbook.entry"
    _description = "CashBook Entry"
    _order = "entry_datetime desc, id desc"

    book_id = fields.Many2one(
        "cashbook.book",
        required=True,
        ondelete="cascade",
        index=True,
    )
    business_id = fields.Many2one(
        "cashbook.business",
        related="book_id.business_id",
        store=True,
        index=True,
    )
    entry_type_id = fields.Many2one(
        "cashbook.entry.type",
        required=True,
        ondelete="restrict",
    )
    direction = fields.Selection(
        selection=[
            ("in", "Cash In"),
            ("out", "Cash Out"),
        ],
        required=True,
        default="in",
        index=True,
    )
    partner_id = fields.Many2one("cashbook.partner")
    entry_datetime = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    line_ids = fields.One2many("cashbook.entry.line", "entry_id")
    payment_ids = fields.One2many("cashbook.payment", "entry_id")
    total_amount = fields.Monetary(
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    paid = fields.Monetary(
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    due = fields.Monetary(
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="business_id.currency_id",
        store=True,
    )
    remarks = fields.Text()
    create_uid = fields.Many2one("res.users", readonly=True)

    @api.depends("line_ids.total_price", "payment_ids.amount")
    def _compute_amounts(self):
        for entry in self:
            entry.total_amount = sum(entry.line_ids.mapped("total_price"))
            entry.paid = sum(entry.payment_ids.mapped("amount"))
            entry.due = entry.total_amount - entry.paid

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_has_lines()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "line_ids" in vals:
            self._check_has_lines()
        return result

    def _check_has_lines(self):
        for entry in self:
            if not entry.line_ids:
                raise ValidationError(
                    _("Each entry must contain at least one entry line.")
                )
