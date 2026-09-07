/** @odoo-module **/

const MENU_ICONS = {
    "cashbook.menu_cashbook_business": "fa-building-o",
    "cashbook.menu_cashbook_book": "fa-book",
    "cashbook.menu_cashbook_entry": "fa-tachometer",
    "cashbook.menu_cashbook_partner": "fa-users",
    "cashbook.menu_cashbook_configuration": "fa-cog",
    "cashbook.menu_cashbook_entry_type": "fa-tags",
    "cashbook.menu_cashbook_payment_method": "fa-credit-card",
};

export function isCashbookApp(menuService) {
    const app = menuService.getCurrentApp();
    return Boolean(app?.xmlid?.startsWith("cashbook."));
}

export function getMenuIcon(menu) {
    return MENU_ICONS[menu?.xmlid] || "fa-circle-o";
}

export function findActiveMenuId(menuService, actionService) {
    const controller = actionService.currentController;
    const actionId = controller?.action?.id;
    if (!actionId) {
        return null;
    }
    const app = menuService.getCurrentApp();
    if (!app) {
        return null;
    }
    const tree = menuService.getMenuAsTree(app.id);

    function walk(menus) {
        for (const menu of menus) {
            if (menu.actionID === actionId) {
                return menu.id;
            }
            if (menu.childrenTree?.length) {
                const found = walk(menu.childrenTree);
                if (found) {
                    return found;
                }
            }
        }
        return null;
    }

    return walk(tree.childrenTree || []);
}
