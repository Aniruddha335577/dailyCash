from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CashbookEntryLine(models.Model):
    _name = "cashbook.entry.line"
    _description = "CashBook Entry Line"
    _order = "id"

    entry_id = fields.Many2one(
        "cashbook.entry",
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_name = fields.Char(required=True)
    product_price = fields.Monetary(required=True, currency_field="currency_id")
    quantity = fields.Float(required=True, default=1.0)
    total_price = fields.Monetary(
        compute="_compute_total_price",
        store=True,
        currency_field="currency_id",
    )
    uom = fields.Char(string="UoM")
    description = fields.Text()
    currency_id = fields.Many2one(
        "res.currency",
        related="entry_id.currency_id",
        store=True,
    )

    @api.depends("product_price", "quantity")
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.product_price * line.quantity

    @api.constrains("quantity", "product_price")
    def _check_line_values(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Line quantity must be greater than zero."))
            if line.product_price < 0:
                raise ValidationError(_("Line price cannot be negative."))
