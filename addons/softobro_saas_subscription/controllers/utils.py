from contextlib import contextmanager

from odoo import api
from odoo.http import request
from odoo.modules.registry import Registry
from odoo.tools import config

IT_SUPPORT_GROUP = "softobro_saas_subscription.group_it_support"


@contextmanager
def it_database_management_context():
    """Expose full database management to IT support users.

    Odoo is often started with ``-d one_db`` which sets ``db_name`` and makes
    ``list_dbs()`` return only that database. Temporarily lift both restrictions
    while IT support uses the web database manager.
    """
    if not is_it_support_user():
        yield
        return
    previous_list_db = config["list_db"]
    previous_db_name = config.get("db_name")
    config["list_db"] = True
    config["db_name"] = []
    try:
        yield
    finally:
        config["list_db"] = previous_list_db
        config["db_name"] = previous_db_name


def is_it_support_user():
    """True when the current browser session belongs to an IT support user."""
    uid = request.session.uid
    dbname = request.db or request.session.db
    if not uid or not dbname:
        return False
    try:
        env = request.env
        cr = getattr(env, "cr", None)
        if cr is not None and not cr.closed:
            return env["res.users"].sudo().browse(uid).has_group(IT_SUPPORT_GROUP)
    except Exception:
        pass
    try:
        with Registry(dbname).cursor() as cr:
            return api.Environment(cr, uid, {}).user.has_group(IT_SUPPORT_GROUP)
    except Exception:
        return False


def saas_platform_locked():
    """True when the current session user must not access Apps / Settings."""
    uid = request.session.uid
    dbname = request.db or request.session.db
    if not uid or not dbname:
        return False
    try:
        env = request.env
        cr = getattr(env, "cr", None)
        if cr is not None and not cr.closed:
            return env["saas.platform.mixin"].saas_platform_locked(
                env["res.users"].browse(uid)
            )
    except Exception:
        pass
    try:
        with Registry(dbname).cursor() as cr:
            env = api.Environment(cr, uid, {})
            return env["saas.platform.mixin"].saas_platform_locked(env.user)
    except Exception:
        return False


def saas_platform_path_blocked(subpath):
    """Return True for Odoo platform URLs that subscribers must not open."""
    try:
        return request.env["saas.platform.mixin"].saas_path_blocked(subpath)
    except Exception:
        return False


def saas_subscriber_home_url():
    try:
        return request.env["saas.platform.mixin"].saas_subscriber_home_url()
    except Exception:
        return "/odoo"


def saas_database_ui_blocked():
    """Return True when the web database manager must not be exposed."""
    if str(config.get("saas_allow_database_manager", "")).lower() in ("1", "true", "yes"):
        return False
    if is_it_support_user():
        return False
    if request.db:
        return (
            request.env["ir.config_parameter"].sudo().get_param("saas.tenant_mode", "True")
            == "True"
        )
    return True
