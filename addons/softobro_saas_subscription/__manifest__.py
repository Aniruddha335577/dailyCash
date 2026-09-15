{
    "name": "SoftoBRo SaaS Subscription",
    "version": "19.0.1.0.11",
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
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/saas_subscription_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "softobro_saas_subscription/static/src/saas_lockdown.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
