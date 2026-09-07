def post_init_hook(env):
    env["cashbook.partner"]._migrate_legacy_types()
