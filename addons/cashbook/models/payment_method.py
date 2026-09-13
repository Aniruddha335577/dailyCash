from odoo import fields, models


class CashbookPaymentMethod(models.Model):
    _name = "cashbook.payment.method"
    _description = "CashBook Payment Method"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
