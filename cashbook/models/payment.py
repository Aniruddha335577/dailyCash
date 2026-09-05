from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CashbookPayment(models.Model):
    _name = "cashbook.payment"
    _description = "CashBook Payment"
    _order = "payment_datetime desc, id desc"

    entry_id = fields.Many2one(
        "cashbook.entry",
        required=True,
        ondelete="cascade",
        index=True,
    )
    payment_method_id = fields.Many2one(
        "cashbook.payment.method",
        required=True,
        ondelete="restrict",
    )
    amount = fields.Monetary(required=True, currency_field="currency_id")
    payment_datetime = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="entry_id.currency_id",
        store=True,
    )
    remarks = fields.Text()

    @api.constrains("amount")
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_("Payment amount must be greater than zero."))

    @api.constrains("amount", "entry_id")
    def _check_total_payments(self):
        for payment in self:
            if not payment.entry_id:
                continue
            total_paid = sum(payment.entry_id.payment_ids.mapped("amount"))
            if total_paid > payment.entry_id.total_amount:
                raise ValidationError(
                    _(
                        "Total payments (%(paid)s) cannot exceed entry total (%(total)s).",
                        paid=total_paid,
                        total=payment.entry_id.total_amount,
                    )
                )
