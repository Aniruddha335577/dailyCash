/** @odoo-module **/

import { session } from "@web/session";

/**
 * Classic Odoo list/form views are for IT support staff only on SaaS tenants.
 * When the SaaS module is not installed, keep Classic View available (local dev).
 */
export function showClassicView() {
    if (!("saas_platform_locked" in session)) {
        return true;
    }
    return Boolean(session.saas_it_support);
}
