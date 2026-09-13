from odoo import http
from odoo.addons.web.controllers.database import Database
from werkzeug.exceptions import NotFound

from .utils import it_database_management_context, saas_database_ui_blocked


class SaasDatabase(Database):
    """Block web database manager routes on SaaS tenant instances."""

    def _deny_database_ui(self):
        if saas_database_ui_blocked():
            raise NotFound()

    def _render_template(self, **d):
        with it_database_management_context():
            return super()._render_template(**d)

    def _dispatch_db_action(self, handler, *args, **kwargs):
        self._deny_database_ui()
        with it_database_management_context():
            return handler(*args, **kwargs)

    @http.route("/web/database/selector", type="http", auth="none")
    def selector(self, **kw):
        self._deny_database_ui()
        # Do not close request.env.cr here: when the IT user is logged in,
        # post_dispatch still needs a live cursor to rotate the session.
        return self._render_template(manage=False)

    @http.route("/web/database/manager", type="http", auth="none")
    def manager(self, **kw):
        self._deny_database_ui()
        return self._render_template()

    @http.route("/web/database/create", type="http", auth="none", methods=["POST"], csrf=False)
    def create(self, master_pwd, name, lang, password, **post):
        return self._dispatch_db_action(
            super().create, master_pwd, name, lang, password, **post
        )

    @http.route("/web/database/duplicate", type="http", auth="none", methods=["POST"], csrf=False)
    def duplicate(self, master_pwd, name, new_name, neutralize_database=False):
        return self._dispatch_db_action(
            super().duplicate,
            master_pwd,
            name,
            new_name,
            neutralize_database=neutralize_database,
        )

    @http.route("/web/database/drop", type="http", auth="none", methods=["POST"], csrf=False)
    def drop(self, master_pwd, name):
        return self._dispatch_db_action(super().drop, master_pwd, name)

    @http.route("/web/database/backup", type="http", auth="none", methods=["POST"], csrf=False)
    def backup(self, master_pwd, name, backup_format="zip", filestore=True):
        return self._dispatch_db_action(
            super().backup,
            master_pwd,
            name,
            backup_format=backup_format,
            filestore=filestore,
        )

    @http.route(
        "/web/database/restore",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
        max_content_length=None,
    )
    def restore(self, master_pwd, backup_file, name, copy=False, neutralize_database=False):
        return self._dispatch_db_action(
            super().restore,
            master_pwd,
            backup_file,
            name,
            copy=copy,
            neutralize_database=neutralize_database,
        )

    @http.route("/web/database/change_password", type="http", auth="none", methods=["POST"], csrf=False)
    def change_password(self, master_pwd, master_pwd_new):
        return self._dispatch_db_action(super().change_password, master_pwd, master_pwd_new)

    @http.route("/web/database/list", type="jsonrpc", auth="none")
    def list(self):
        return self._dispatch_db_action(super().list)
