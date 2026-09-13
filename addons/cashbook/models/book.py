import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


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
    phone_1 = fields.Char(string="Phone 1")
    phone_2 = fields.Char(string="Phone 2")
    email = fields.Char(string="Email")
    active = fields.Boolean(default=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="business_id.currency_id",
        store=True,
    )

    @api.constrains("email")
    def _check_email(self):
        for book in self.filtered("email"):
            if not _EMAIL_RE.match(book.email.strip()):
                raise ValidationError(_("Enter a valid email address."))
