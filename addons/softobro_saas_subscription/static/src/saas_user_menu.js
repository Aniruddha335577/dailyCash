/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { UserMenu } from "@web/webclient/user_menu/user_menu";

/** Hidden for tenant subscribers (IT support keeps full menu). */
const BLOCKED_USER_MENU_IDS = new Set([
    "support",
    "shortcuts",
    "separator",
    "preferences",
    "odoo_account",
]);

function lockDownUserMenuItems() {
    if (!session.saas_platform_locked) {
        return;
    }
    const menuItems = registry.category("user_menuitems");
    for (const id of BLOCKED_USER_MENU_IDS) {
        if (!menuItems.contains(id)) {
            continue;
        }
        const factory = menuItems.get(id);
        menuItems.add(
            id,
            (env) => {
                const item = factory(env);
                return {
                    ...item,
                    show: () => false,
                };
            },
            { force: true }
        );
    }
}

patch(UserMenu.prototype, {
    get saasHideDatabaseLabel() {
        return Boolean(session.saas_platform_locked);
    },
});

lockDownUserMenuItems();
