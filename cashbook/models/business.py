from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .saas_restriction import check_business_creation_allowed


class CashbookBusiness(models.Model):
    _name = "cashbook.business"
    _description = "CashBook Business"
    _order = "name"

    name = fields.Char(required=True)
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    active = fields.Boolean(default=True)
    book_ids = fields.One2many("cashbook.book", "business_id")

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
