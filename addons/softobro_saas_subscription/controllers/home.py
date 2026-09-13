from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound

from .utils import is_it_support_user


class SaasHome(http.Controller):
    """Redirect IT support users out of the /odoo SPA to the database manager page."""

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
