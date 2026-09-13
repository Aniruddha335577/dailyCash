# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaasSubscriptionRestriction(models.Model):
    _name = "saas.subscription.restriction"
    _description = "SaaS Subscription Restriction"
    _rec_name = "code"

    subscription_id = fields.Many2one(
        "saas.subscription",
        required=True,
        ondelete="cascade",
        index=True,
    )
    code = fields.Char(required=True, index=True)
    value_type = fields.Selection(
        selection=[
            ("integer", "Integer"),
            ("unlimited", "Unlimited"),
        ],
        required=True,
        default="integer",
    )
    value_int = fields.Integer()

    _sql_constraints = [
        (
            "subscription_restriction_unique",
            "unique(subscription_id, code)",
            "Restriction code must be unique per subscription.",
        ),
    ]
