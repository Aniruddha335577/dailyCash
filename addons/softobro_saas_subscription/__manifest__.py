{
    "name": "SoftoBRo SaaS Subscription",
    "version": "19.0.1.0.7",
    "category": "Hidden",
    "summary": "Tenant subscription entitlements, provisioner API, and user-limit enforcement",
    "license": "LGPL-3",
    "author": "SoftoBRo",
    "depends": [
        "base",
        "web",
        "auth_signup",
        "mail",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/saas_subscription_views.xml",
    ],
    "installable": True,
    "application": False,
}
