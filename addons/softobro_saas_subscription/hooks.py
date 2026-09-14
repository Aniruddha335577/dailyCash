def post_init_hook(env):
    env["res.users"]._saas_apply_subscriber_lockdown_all()
