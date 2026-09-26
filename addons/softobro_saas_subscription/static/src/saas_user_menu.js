/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { UserMenu } from "@web/webclient/user_menu/user_menu";

/** Profile menu entries hidden for tenant subscribers (IT support keeps full menu). */
const SUBSCRIBER_HIDDEN_MENU_IDS = new Set([
    "support",
    "shortcuts",
    "preferences",
    "odoo_account",
    "install_pwa",
]);

function subscriberMenuLocked() {
    return Boolean(session.saas_platform_locked);
}

function filterSubscriberUserMenu(elements) {
    return elements.filter((element) => {
        if (element.type === "separator") {
            return false;
        }
        if (element.id && SUBSCRIBER_HIDDEN_MENU_IDS.has(element.id)) {
            return false;
        }
        return true;
    });
}

patch(UserMenu.prototype, {
    getElements() {
        const elements = super.getElements(...arguments);
        if (!subscriberMenuLocked()) {
            return elements;
        }
        return filterSubscriberUserMenu(elements);
    },

    get saasHideDatabaseLabel() {
        return subscriberMenuLocked();
    },
});
