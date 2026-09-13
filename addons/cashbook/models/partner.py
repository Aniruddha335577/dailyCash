from odoo import api, fields, models


class CashbookPartner(models.Model):
    _name = "cashbook.partner"
    _description = "CashBook Partner"
    _order = "name"

    name = fields.Char(required=True)
    partner_type = fields.Selection(
        selection=[
            ("customer", "Customer"),
            ("vendor", "Vendor"),
        ],
        required=True,
        default="customer",
    )
    phone = fields.Char()
    notes = fields.Text()
    active = fields.Boolean(default=True)

    @api.model
    def _migrate_legacy_types(self):
        """Convert removed 'both' partner type to customer."""
        self.env.cr.execute(
            "UPDATE cashbook_partner SET partner_type = 'customer' WHERE partner_type = 'both'"
        )
