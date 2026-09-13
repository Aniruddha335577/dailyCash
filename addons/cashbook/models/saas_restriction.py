"""Optional SaaS package restriction integration.

CashBook consumes limits from saas.subscription when that module is installed.
No package data is stored in CashBook.
"""

from odoo import _
from odoo.exceptions import ValidationError

RESTRICTION_CODE = "cashbook.business"


def check_business_creation_allowed(env, additional=1):
    """Raise ValidationError if creating additional businesses exceeds the package limit."""
    if "saas.subscription" not in env:
        return

    subscription = env["saas.subscription"].sudo().search([], limit=1)
    if not subscription:
        return

    if subscription.status in {"suspended", "cancelled", "expired"}:
        raise ValidationError(
            _("Cannot create a business while the subscription is %(status)s."),
            status=dict(subscription._fields["status"].selection).get(
                subscription.status, subscription.status
            ),
        )

    limit = subscription.get_limit(RESTRICTION_CODE)
    if limit is None:
        return

    current_count = env["cashbook.business"].sudo().search_count([("active", "=", True)])
    if current_count + additional > limit:
        raise ValidationError(
            _(
                "Business limit reached: %(usage)s / %(limit)s. "
                "Contact your administrator to upgrade your package.",
                usage=current_count,
                limit=limit,
            )
        )
