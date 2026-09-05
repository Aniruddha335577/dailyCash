from odoo import fields, models


class CashbookEntryType(models.Model):
    _name = "cashbook.entry.type"
    _description = "CashBook Entry Type"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
