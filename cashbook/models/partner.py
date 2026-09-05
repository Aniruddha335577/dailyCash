from odoo import fields, models


class CashbookPartner(models.Model):
    _name = "cashbook.partner"
    _description = "CashBook Partner"
    _order = "name"

    name = fields.Char(required=True)
    partner_type = fields.Selection(
        selection=[
            ("customer", "Customer"),
            ("vendor", "Vendor"),
            ("both", "Both"),
        ],
        required=True,
        default="customer",
    )
    phone = fields.Char()
    notes = fields.Text()
    active = fields.Boolean(default=True)
