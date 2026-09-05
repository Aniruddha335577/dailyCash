from odoo import fields, models


class CashbookBook(models.Model):
    _name = "cashbook.book"
    _description = "CashBook Book"
    _order = "name"

    business_id = fields.Many2one(
        "cashbook.business",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="business_id.currency_id",
        store=True,
    )
