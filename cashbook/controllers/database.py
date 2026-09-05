from odoo import http
from odoo.addons.web.controllers.database import Database
from odoo.http import request

from .utils import cashbook_saas_mode


class CashbookDatabase(Database):
    @http.route()
    def selector(self, **kw):
        if cashbook_saas_mode():
            return request.redirect("/web/login")
        return super().selector(**kw)

    @http.route()
    def manager(self, **kw):
        if cashbook_saas_mode():
            return request.redirect("/web/login")
        return super().manager(**kw)
