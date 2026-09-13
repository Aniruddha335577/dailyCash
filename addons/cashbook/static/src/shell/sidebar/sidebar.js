/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { findActiveMenuId, getMenuIcon } from "../utils/shell_utils";

export class CashbookSidebar extends Component {
    static template = "cashbook.Sidebar";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.state = useState({
            expanded: {},
            revision: 0,
        });

        const bump = () => {
            this.state.revision++;
        };
        useBus(this.env.bus, "MENUS:APP-CHANGED", bump);
        useBus(this.env.bus, "ACTION_MANAGER:UPDATE", bump);
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", bump);
    }

    get sections() {
        this.state.revision;
        const app = this.menuService.getCurrentApp();
        if (!app) {
            return [];
        }
        return this.menuService.getMenuAsTree(app.id).childrenTree || [];
    }

    get activeMenuId() {
        this.state.revision;
        return findActiveMenuId(this.menuService, this.actionService);
    }

    getIcon(menu) {
        return getMenuIcon(menu);
    }

    isActive(menu) {
        return menu.id === this.activeMenuId;
    }

    isChildActive(menu) {
        if (!menu.childrenTree?.length) {
            return false;
        }
        return menu.childrenTree.some((child) => child.id === this.activeMenuId);
    }

    isExpanded(menu) {
        if (this.state.expanded[menu.id] !== undefined) {
            return this.state.expanded[menu.id];
        }
        return this.isChildActive(menu);
    }

    toggleExpand(menu, ev) {
        ev.stopPropagation();
        this.state.expanded[menu.id] = !this.isExpanded(menu);
    }

    onSelectMenu(menu) {
        if (menu?.actionID) {
            this.menuService.selectMenu(menu);
        }
    }
}
