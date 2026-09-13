# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaasSubscriptionFeature(models.Model):
    _name = "saas.subscription.feature"
    _description = "SaaS Subscription Feature"
    _rec_name = "code"

    subscription_id = fields.Many2one(
        "saas.subscription",
        required=True,
        ondelete="cascade",
        index=True,
    )
    code = fields.Char(required=True, index=True)
    enabled = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "subscription_feature_unique",
            "unique(subscription_id, code)",
            "Feature code must be unique per subscription.",
        ),
    ]
