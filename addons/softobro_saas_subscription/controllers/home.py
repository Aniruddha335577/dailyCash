from odoo import http
from odoo.addons.web.controllers import home as web_home
from odoo.http import request, route
from werkzeug.exceptions import NotFound

from .utils import (
    is_it_support_user,
    saas_platform_locked,
    saas_platform_path_blocked,
    saas_subscriber_home_url,
)


class Home(web_home.Home):
    @route()
    def web_client(self, s_action=None, subpath=None, **kw):
        if saas_platform_locked() and subpath and saas_platform_path_blocked(subpath):
            return request.redirect(saas_subscriber_home_url())
        return super().web_client(s_action=s_action, subpath=subpath, **kw)

    @http.route(
        ["/odoo/database/manager", "/odoo/web/database/manager"],
        type="http",
        auth="user",
        methods=["GET"],
    )
    def it_database_manager_redirect(self, **kw):
        if not is_it_support_user():
            raise NotFound()
        return request.redirect("/web/database/manager")
