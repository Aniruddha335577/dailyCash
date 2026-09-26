# Part of SoftoBRo. See LICENSE file for full copyright and licensing details.

import json
import logging
import random
import secrets
from pathlib import Path

from odoo import Command, _, api, fields, models
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.exceptions import AccessDenied, UserError, ValidationError

_logger = logging.getLogger(__name__)

MASTER_KEY_PARAM = "saas.provisioner.master_key"
API_KEY_PARAM = "saas.provisioner.api_key"
ADMIN_EMAIL_PARAM = "saas.provisioner.admin_email"
ADMIN_USER_ID_PARAM = "saas.provisioner.admin_user_id"
TENANT_PUBLIC_URL_PARAM = "saas.tenant.public_url"

FEATURE_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "feature_module_map.json"


class SaasSubscription(models.Model):
    _name = "saas.subscription"
    _description = "SaaS Tenant Subscription"
    _rec_name = "tenant_slug"

    tenant_slug = fields.Char(required=True, index=True)
    package_code = fields.Char(index=True)
    package_version = fields.Integer(default=0)
    configuration_revision = fields.Integer(default=0, index=True)
    status = fields.Selection(
        selection=[
            ("trial", "Trial"),
            ("active", "Active"),
            ("past_due", "Past Due"),
            ("suspended", "Suspended"),
            ("cancelled", "Cancelled"),
            ("expired", "Expired"),
        ],
        default="active",
        required=True,
        index=True,
    )
    over_limit = fields.Boolean(default=False, readonly=True)
    admin_email = fields.Char()
    admin_user_id = fields.Many2one("res.users", readonly=True)
    feature_ids = fields.One2many("saas.subscription.feature", "subscription_id")
    restriction_ids = fields.One2many("saas.subscription.restriction", "subscription_id")
    last_update_at = fields.Datetime(readonly=True)

    _sql_constraints = [
        (
            "tenant_slug_unique",
            "unique(tenant_slug)",
            "Only one subscription record is allowed per tenant slug.",
        ),
    ]

    @api.model
    def _load_feature_module_map(self) -> dict[str, str]:
        if not FEATURE_MAP_PATH.is_file():
            return {}
        return json.loads(FEATURE_MAP_PATH.read_text(encoding="utf-8"))

    @api.model
    def _get_singleton(self):
        sub = self.search([], limit=1)
        if not sub:
            raise UserError(_("SaaS subscription is not initialized for this tenant."))
        return sub

    @api.model
    def service(self):
        return self._get_singleton()

    def has_feature(self, feature_code: str) -> bool:
        self.ensure_one()
        feature = self.feature_ids.filtered(lambda f: f.code == feature_code)[:1]
        return bool(feature and feature.enabled)

    def get_limit(self, restriction_code: str):
        self.ensure_one()
        restriction = self.restriction_ids.filtered(lambda r: r.code == restriction_code)[:1]
        if not restriction:
            return None
        if restriction.value_type == "unlimited":
            return None
        return restriction.value_int

    def get_usage(self, restriction_code: str) -> int:
        self.ensure_one()
        if restriction_code == "users":
            return self.env["res.users"].sudo().search_count(self._user_limit_domain())
        return 0

    def can_create(self, restriction_code: str) -> bool:
        self.ensure_one()
        if self.status in {"suspended", "cancelled", "expired"}:
            return False
        limit = self.get_limit(restriction_code)
        if limit is None:
            return True
        return self.get_usage(restriction_code) < limit

    def check_limit(self, restriction_code: str):
        self.ensure_one()
        if not self.can_create(restriction_code):
            limit = self.get_limit(restriction_code)
            usage = self.get_usage(restriction_code)
            raise UserError(
                _(
                    "Limit reached for %(code)s: %(usage)s / %(limit)s.",
                    code=restriction_code,
                    usage=usage,
                    limit=limit,
                )
            )

    def require_feature(self, feature_code: str):
        self.ensure_one()
        if not self.has_feature(feature_code):
            raise AccessDenied(_("Feature '%(feature)s' is not enabled.", feature=feature_code))

    @api.model
    def _user_limit_domain(self):
        return [
            ("active", "=", True),
            ("share", "in", [False, True]),
            ("id", "!=", 1),
        ]

    @api.model
    def _normalize_email(self, value: str) -> str:
        email = (value or "").strip().lower()
        while len(email) >= 2 and email[0] == email[-1] and email[0] in "'\"":
            email = email[1:-1].strip().lower()
        return email

    @api.model
    def _get_or_create_admin_user(self, name: str, email: str):
        email = self._normalize_email(email)
        Users = self.env["res.users"].sudo()
        admin = Users.search([("login", "=", email)], limit=1)
        if admin:
            admin.write({"name": name, "email": email, "active": True})
            return admin

        group_subscriber_admin = self.env.ref(
            "softobro_saas_subscription.group_subscriber_admin"
        )
        return Users.with_context(no_reset_password=True).create({
            "name": name,
            "login": email,
            "email": email,
            "group_ids": [Command.set([group_subscriber_admin.id])],
            "active": True,
        })

    @api.model
    def _generate_api_key(self) -> str:
        return secrets.token_urlsafe(32)

    @api.model
    def _set_config_param(self, key: str, value: str):
        self.env["ir.config_parameter"].sudo().set_param(key, value or "")

    @api.model
    def _ensure_saas_url_config(self):
        icp = self.env["ir.config_parameter"].sudo()
        defaults = {
            "saas.public_base_domain": "softobro.com",
            "saas.tenant_url_suffix": "-hishabbro",
            "saas.public_url_scheme": "https",
        }
        for key, value in defaults.items():
            if not icp.get_param(key):
                icp.set_param(key, value)

    @api.model
    def _resolve_public_base_url(self) -> str:
        """Canonical HTTPS origin for emails and signup links (never localhost from template)."""
        icp = self.env["ir.config_parameter"].sudo()
        stored = (icp.get_param(TENANT_PUBLIC_URL_PARAM) or "").strip().rstrip("/")
        if stored:
            return stored
        base = (icp.get_param("web.base.url") or "").strip().rstrip("/")
        if base and "localhost" not in base and "127.0.0.1" not in base:
            return base
        subscription = self.search([], limit=1)
        slug = subscription.tenant_slug if subscription else self.env.cr.dbname
        derived = self._derive_tenant_public_url(slug)
        return derived or base

    @api.model
    def _normalize_public_url(self, url: str) -> str:
        url = (url or "").strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise ValidationError(_("Tenant public URL must start with http:// or https://."))
        return url

    @api.model
    def _set_tenant_public_url(self, url: str):
        """Canonical tenant URL for emails (web.base.url + signup links)."""
        url = self._normalize_public_url(url)
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param(TENANT_PUBLIC_URL_PARAM, url)
        icp.set_param("web.base.url", url)

    @api.model
    def _derive_tenant_public_url(self, tenant_slug: str) -> str | None:
        icp = self.env["ir.config_parameter"].sudo()
        domain = (icp.get_param("saas.public_base_domain") or "").strip().lstrip(".")
        if not domain or not tenant_slug:
            return None
        suffix = icp.get_param("saas.tenant_url_suffix") or ""
        scheme = (icp.get_param("saas.public_url_scheme") or "https").strip().rstrip(":/")
        return f"{scheme}://{tenant_slug}{suffix}.{domain}".rstrip("/")

    @api.model
    def _ensure_tenant_public_url(self, url: str | None = None):
        self._ensure_saas_url_config()
        if url:
            self._set_tenant_public_url(url)
            return
        icp = self.env["ir.config_parameter"].sudo()
        stored = (icp.get_param(TENANT_PUBLIC_URL_PARAM) or "").strip().rstrip("/")
        if stored:
            if (icp.get_param("web.base.url") or "").strip().rstrip("/") != stored:
                icp.set_param("web.base.url", stored)
            return
        base = icp.get_param("web.base.url") or ""
        if "localhost" in base or "127.0.0.1" in base or not base.strip():
            subscription = self.search([], limit=1)
            slug = subscription.tenant_slug if subscription else self.env.cr.dbname
            derived = self._derive_tenant_public_url(slug)
            if derived:
                self._set_tenant_public_url(derived)

    @api.model
    def _disable_shared_admins(self, admin_email: str, shared_logins: list[str] | None = None):
        logins = shared_logins or ["admin"]
        users = self.env["res.users"].sudo().search([
            ("login", "in", logins),
            ("active", "=", True),
        ])
        it_support_group = self.env.ref(
            "softobro_saas_subscription.group_it_support",
            raise_if_not_found=False,
        )
        for user in users:
            if user.login == admin_email or user.id == 1:
                continue
            if it_support_group and it_support_group in user.group_ids:
                continue
            user.write({"active": False})

    @api.model
    def _ensure_outbound_mail_identity(self):
        """Provision/shell runs without a logged-in user; avoid catchall@ / empty From."""
        icp = self.env["ir.config_parameter"].sudo()
        brand = icp.get_param("cashbook.brand_name") or "HisabBro"
        outbound = "noreply@softobro.com"
        company = self.env.company.sudo()
        partner = company.partner_id
        if partner.email != outbound:
            partner.write({"email": outbound})
        if not company.name or company.name == "My Company":
            company.write({"name": brand})
        for alias_domain in self.env["mail.alias.domain"].sudo().search([]):
            if alias_domain.default_from_email != outbound:
                alias_domain.write({"default_from": outbound})

    @api.model
    def _apply_hishabbro_invite_templates(self):
        try:
            from odoo.addons.cashbook.hooks import apply_hishabbro_invite_mail_templates

            apply_hishabbro_invite_mail_templates(self.env)
        except ImportError:
            _logger.warning("cashbook not installed; HisabBro invite templates not applied")

    @api.model
    def _send_invitation_email(self, user):
        """Send signup invite (same template as UI). Shell/Postman must set From + templates first."""
        self._ensure_tenant_public_url()
        self._ensure_outbound_mail_identity()
        self._apply_hishabbro_invite_templates()
        if not user.email:
            _logger.warning("Invitation skipped: user %s has no email", user.login)
            return "email_failed"

        Mail = self.env["mail.mail"].sudo()
        before_ids = set(Mail.search([("email_to", "=", user.email)]).ids)
        try:
            # Odoo 19 checks create_user == 1 (not truthy-only in all code paths).
            user.with_context(create_user=1).action_reset_password()
        except (UserError, MailDeliveryException) as exc:
            _logger.warning("Invitation email failed for %s: %s", user.login, exc)
            return "email_failed"

        failed = Mail.search([
            ("email_to", "=", user.email),
            ("id", "not in", list(before_ids)),
            ("state", "=", "exception"),
        ], limit=1)
        if failed:
            _logger.warning(
                "Invitation mail in exception for %s: %s",
                user.login,
                failed.failure_reason or failed.failure_type,
            )
            return "email_failed"
        return "sent"

    @api.model
    def provisioner_initialize_tenant(self, tenant_slug: str, tenant_public_url: str):
        """Run right after pg_restore: URL + SaaS URL config before any mail."""
        self._ensure_saas_url_config()
        self._set_tenant_public_url(tenant_public_url)
        subscription = self.search([], limit=1)
        if subscription:
            subscription.write({"tenant_slug": tenant_slug, "status": "active"})
        else:
            self.create({
                "tenant_slug": tenant_slug,
                "status": "active",
            })
        icp = self.env["ir.config_parameter"].sudo()
        return {
            "ok": True,
            "tenant_slug": tenant_slug,
            "web_base_url": icp.get_param("web.base.url"),
        }

    @api.model
    def provisioner_onboard(
        self,
        tenant_slug: str,
        customer_name: str,
        customer_email: str,
        shared_admin_logins: list[str] | None = None,
        tenant_public_url: str | None = None,
    ):
        customer_email = self._normalize_email(customer_email)
        if not customer_email:
            raise ValidationError(_("Customer email is required."))

        self._ensure_tenant_public_url(tenant_public_url)

        subscription = self.search([("tenant_slug", "=", tenant_slug)], limit=1)
        if not subscription:
            subscription = self.create({
                "tenant_slug": tenant_slug,
                "status": "active",
                "admin_email": customer_email,
            })
        else:
            subscription.write({"admin_email": customer_email})

        admin_user = self._get_or_create_admin_user(customer_name, customer_email)
        self._disable_shared_admins(customer_email, shared_admin_logins)

        api_key = self._generate_api_key()
        self._set_config_param(API_KEY_PARAM, api_key)
        self._set_config_param(ADMIN_EMAIL_PARAM, customer_email)
        self._set_config_param(ADMIN_USER_ID_PARAM, str(admin_user.id))

        self._ensure_outbound_mail_identity()
        invitation_status = self._send_invitation_email(admin_user)
        subscription.write({
            "admin_user_id": admin_user.id,
            "admin_email": customer_email,
        })

        return {
            "ok": True,
            "tenant_slug": tenant_slug,
            "admin_email": customer_email,
            "admin_user_id": admin_user.id,
            "odoo_api_key": api_key,
            "invitation_status": invitation_status,
        }

    @api.model
    def provisioner_resend_invitation(self, email: str, tenant_public_url: str | None = None):
        email = self._normalize_email(email)
        if not email:
            raise ValidationError(_("Email is required."))

        self._ensure_tenant_public_url(tenant_public_url)

        subscription = self._get_singleton()
        admin_user = subscription.admin_user_id
        if not admin_user:
            admin_user = self.env["res.users"].sudo().search([("login", "=", email)], limit=1)
        if not admin_user:
            raise UserError(_("Provisioned admin user was not found."))

        if admin_user.login != email:
            admin_user.write({"login": email, "email": email})
        subscription.write({"admin_email": email})
        self._set_config_param(ADMIN_EMAIL_PARAM, email)
        self._set_config_param(ADMIN_USER_ID_PARAM, str(admin_user.id))

        invitation_status = self._send_invitation_email(admin_user)
        return {
            "ok": True,
            "admin_email": email,
            "invitation_status": invitation_status,
        }

    def _merge_features(self, features: dict | None):
        self.ensure_one()
        if not features:
            return
        Feature = self.env["saas.subscription.feature"].sudo()
        for code, enabled in features.items():
            row = Feature.search([("subscription_id", "=", self.id), ("code", "=", code)], limit=1)
            vals = {"enabled": bool(enabled)}
            if row:
                row.write(vals)
            else:
                Feature.create({"subscription_id": self.id, "code": code, **vals})

    def _merge_restrictions(self, restrictions: dict | None):
        self.ensure_one()
        if not restrictions:
            return
        Restriction = self.env["saas.subscription.restriction"].sudo()
        for code, raw_value in restrictions.items():
            if isinstance(raw_value, dict):
                value_type = raw_value.get("value_type") or "integer"
                value_int = raw_value.get("value")
            elif raw_value is None:
                value_type = "unlimited"
                value_int = False
            else:
                value_type = "integer"
                value_int = int(raw_value)
            row = Restriction.search([("subscription_id", "=", self.id), ("code", "=", code)], limit=1)
            vals = {"value_type": value_type, "value_int": value_int or 0}
            if row:
                row.write(vals)
            else:
                Restriction.create({"subscription_id": self.id, "code": code, **vals})

    def _install_enabled_features(self, previous_features: dict[str, bool]):
        self.ensure_one()
        module_map = self._load_feature_module_map()
        Module = self.env["ir.module.module"].sudo()
        to_install = Module.browse()
        for feature in self.feature_ids:
            was_enabled = previous_features.get(feature.code, False)
            if feature.enabled and not was_enabled:
                module_name = module_map.get(feature.code)
                if not module_name:
                    continue
                mod = Module.search([("name", "=", module_name), ("state", "!=", "installed")], limit=1)
                if mod:
                    to_install |= mod
        if to_install:
            to_install.button_immediate_install()

    def _apply_user_downgrade(self):
        self.ensure_one()
        limit = self.get_limit("users")
        if limit is None:
            self.over_limit = False
            return

        Users = self.env["res.users"].sudo()
        active_users = Users.search(self._user_limit_domain())
        if len(active_users) <= limit:
            self.over_limit = False
            return

        protected_ids = {1}
        if self.admin_user_id:
            protected_ids.add(self.admin_user_id.id)
        else:
            admin_email = self.admin_email or self.env["ir.config_parameter"].sudo().get_param(ADMIN_EMAIL_PARAM)
            if admin_email:
                admin = Users.search([("login", "=", admin_email)], limit=1)
                if admin:
                    protected_ids.add(admin.id)

        keep_ids = set()
        for uid in protected_ids:
            user = Users.browse(uid)
            if user.exists() and user.active and uid not in keep_ids:
                keep_ids.add(uid)

        remaining_slots = max(limit - len(keep_ids), 0)
        pool = active_users.filtered(lambda u: u.id not in keep_ids)
        if remaining_slots > 0 and pool:
            picked = random.sample(list(pool.ids), min(remaining_slots, len(pool)))
            keep_ids.update(picked)

        archive_users = active_users.filtered(lambda u: u.id not in keep_ids)
        if archive_users:
            archive_users.write({"active": False})

        still_active = Users.search_count(self._user_limit_domain())
        self.over_limit = still_active > limit

    @api.model
    def provisioner_package_update(self, payload: dict):
        subscription = self._get_singleton()
        incoming_revision = int(payload.get("configuration_revision") or 0)
        if incoming_revision <= 0:
            raise ValidationError(_("configuration_revision must be a positive integer."))
        if incoming_revision <= subscription.configuration_revision:
            return {
                "ok": True,
                "idempotent": True,
                "configuration_revision": subscription.configuration_revision,
                "status": subscription.status,
            }

        previous_features = {f.code: f.enabled for f in subscription.feature_ids}
        previous_user_limit = subscription.get_limit("users")

        write_vals = {
            "configuration_revision": incoming_revision,
            "last_update_at": fields.Datetime.now(),
        }
        if payload.get("package_code"):
            write_vals["package_code"] = payload["package_code"]
        if payload.get("package_version") is not None:
            write_vals["package_version"] = int(payload["package_version"])
        subscription.write(write_vals)
        subscription._merge_features(payload.get("features"))
        subscription._merge_restrictions(payload.get("restrictions"))
        subscription._install_enabled_features(previous_features)

        new_user_limit = subscription.get_limit("users")
        if new_user_limit is not None and (
            previous_user_limit is None or new_user_limit < previous_user_limit
        ):
            subscription._apply_user_downgrade()
        else:
            subscription.over_limit = False

        return {
            "ok": True,
            "configuration_revision": subscription.configuration_revision,
            "package_code": subscription.package_code,
            "package_version": subscription.package_version,
            "over_limit": subscription.over_limit,
            "status": subscription.status,
        }

    @api.model
    def provisioner_set_status(self, status: str):
        subscription = self._get_singleton()
        if status not in dict(subscription._fields["status"].selection):
            raise ValidationError(_("Invalid subscription status: %s") % status)
        subscription.write({"status": status})
        return {"ok": True, "status": subscription.status}
