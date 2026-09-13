# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

import json
import logging

from odoo import SUPERUSER_ID, api, http
from odoo.exceptions import AccessDenied, UserError, ValidationError
from odoo.http import request
from odoo.modules.registry import Registry

from ..models.saas_subscription import ADMIN_EMAIL_PARAM, API_KEY_PARAM, MASTER_KEY_PARAM

_logger = logging.getLogger(__name__)


class SaasProvisionerController(http.Controller):

    def _open_env(self, db_name):
        if not db_name:
            raise ValidationError("missing_db")
        registry = Registry(db_name)
        cr = registry.cursor()
        env = api.Environment(cr, SUPERUSER_ID, {})
        return env, cr

    def _ensure_saas_module(self, env):
        Module = env["ir.module.module"].sudo()
        Module.update_list()
        module = Module.search([("name", "=", "softobro_saas_subscription")], limit=1)
        if not module:
            raise UserError("Module softobro_saas_subscription was not found on addons_path.")
        if module.state != "installed":
            module.button_immediate_install()
        return env["saas.subscription"].sudo()

    def _parse_json_body(self):
        data = request.httprequest.data
        if not data:
            return {}
        return json.loads(data.decode("utf-8"))

    def _verify_master_key(self, env, provided_key: str | None):
        expected = env["ir.config_parameter"].sudo().get_param(MASTER_KEY_PARAM)
        if not expected or not provided_key or provided_key != expected:
            raise AccessDenied("invalid_master_key")

    def _verify_tenant_key(self, env, provided_key: str | None):
        expected = env["ir.config_parameter"].sudo().get_param(API_KEY_PARAM)
        if not expected or not provided_key or provided_key != expected:
            raise AccessDenied("invalid_api_key")

    def _json_response(self, payload, status=200):
        return request.make_json_response(payload, status=status)

    @http.route("/saas/provisioner/onboard", type="http", auth="none", csrf=False, methods=["POST"])
    def onboard(self, **kwargs):
        db_name = request.httprequest.args.get("db")
        body = self._parse_json_body()
        env, cr = self._open_env(db_name)
        try:
            self._verify_master_key(env, request.httprequest.headers.get("X-Provisioner-Master-Key"))
            Subscription = self._ensure_saas_module(env)
            result = Subscription.provisioner_onboard(
                tenant_slug=body.get("tenant_slug") or db_name,
                customer_name=body.get("customer_name") or "Tenant Admin",
                customer_email=body.get("customer_email") or "",
                shared_admin_logins=body.get("shared_admin_logins"),
            )
            cr.commit()
            return self._json_response(result)
        except AccessDenied:
            cr.rollback()
            return self._json_response({"ok": False, "error": "invalid_master_key"}, status=401)
        except (ValidationError, UserError) as exc:
            cr.rollback()
            return self._json_response({"ok": False, "error": str(exc.args[0])}, status=400)
        except Exception:
            cr.rollback()
            _logger.exception("Onboard failed for db=%s", db_name)
            return self._json_response({"ok": False, "error": "internal_error"}, status=500)
        finally:
            cr.close()

    @http.route("/saas/provisioner/package_update", type="http", auth="none", csrf=False, methods=["POST"])
    def package_update(self, **kwargs):
        db_name = request.httprequest.args.get("db")
        body = self._parse_json_body()
        env, cr = self._open_env(db_name)
        try:
            self._verify_tenant_key(env, request.httprequest.headers.get("X-Saas-Api-Key"))
            Subscription = self._ensure_saas_module(env)
            result = Subscription.provisioner_package_update(body)
            cr.commit()
            return self._json_response(result)
        except AccessDenied:
            cr.rollback()
            return self._json_response({"ok": False, "error": "invalid_api_key"}, status=401)
        except (ValidationError, UserError) as exc:
            cr.rollback()
            return self._json_response({"ok": False, "error": str(exc.args[0])}, status=400)
        except Exception:
            cr.rollback()
            _logger.exception("Package update failed for db=%s", db_name)
            return self._json_response({"ok": False, "error": "internal_error"}, status=500)
        finally:
            cr.close()

    @http.route("/saas/provisioner/invitation_resend", type="http", auth="none", csrf=False, methods=["POST"])
    def invitation_resend(self, **kwargs):
        db_name = request.httprequest.args.get("db")
        body = self._parse_json_body()
        env, cr = self._open_env(db_name)
        try:
            self._verify_tenant_key(env, request.httprequest.headers.get("X-Saas-Api-Key"))
            Subscription = self._ensure_saas_module(env)
            result = Subscription.provisioner_resend_invitation(body.get("email"))
            cr.commit()
            return self._json_response(result)
        except AccessDenied:
            cr.rollback()
            return self._json_response({"ok": False, "error": "invalid_api_key"}, status=401)
        except (ValidationError, UserError) as exc:
            cr.rollback()
            return self._json_response({"ok": False, "error": str(exc.args[0])}, status=400)
        except Exception:
            cr.rollback()
            _logger.exception("Invitation resend failed for db=%s", db_name)
            return self._json_response({"ok": False, "error": "internal_error"}, status=500)
        finally:
            cr.close()

    @http.route("/saas/provisioner/set_status", type="http", auth="none", csrf=False, methods=["POST"])
    def set_status(self, **kwargs):
        db_name = request.httprequest.args.get("db")
        body = self._parse_json_body()
        env, cr = self._open_env(db_name)
        try:
            self._verify_tenant_key(env, request.httprequest.headers.get("X-Saas-Api-Key"))
            Subscription = self._ensure_saas_module(env)
            result = Subscription.provisioner_set_status(body.get("status"))
            cr.commit()
            return self._json_response(result)
        except AccessDenied:
            cr.rollback()
            return self._json_response({"ok": False, "error": "invalid_api_key"}, status=401)
        except (ValidationError, UserError) as exc:
            cr.rollback()
            return self._json_response({"ok": False, "error": str(exc.args[0])}, status=400)
        except Exception:
            cr.rollback()
            _logger.exception("Set status failed for db=%s", db_name)
            return self._json_response({"ok": False, "error": "internal_error"}, status=500)
        finally:
            cr.close()
