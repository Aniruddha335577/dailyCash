/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { ErrorHandler } from "@web/core/utils/components";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { CashbookGlobalSearch } from "../global_search/global_search";
import { CashbookQuickCreate } from "../quick_create/quick_create";
import { CashbookMobileMenu } from "../mobile_menu/mobile_menu";
import { BRAND_LOGO_URL, BRAND_NAME } from "../../utils/brand";
import { isCashbookApp } from "../utils/shell_utils";

const ALLOWED_SYSTRAY_KEYS = new Set(["web.user_menu"]);

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.cbState = useState({
            mobileMenuOpen: false,
        });
        this.brandName = BRAND_NAME;
        this.brandLogoUrl = BRAND_LOGO_URL;
    },

    get useCashbookShell() {
        return isCashbookApp(this.menuService);
    },

    get currentAppSections() {
        if (this.useCashbookShell) {
            return [];
        }
        return super.currentAppSections;
    },

    get systrayItems() {
        const items = super.systrayItems;
        if (!this.useCashbookShell) {
            return items;
        }
        return items.filter((item) => ALLOWED_SYSTRAY_KEYS.has(item.key));
    },

    get cashbookMenuSections() {
        const app = this.menuService.getCurrentApp();
        if (!app) {
            return [];
        }
        return this.menuService.getMenuAsTree(app.id).childrenTree || [];
    },

    openCashbookMobileMenu() {
        this.cbState.mobileMenuOpen = true;
    },

    closeCashbookMobileMenu() {
        this.cbState.mobileMenuOpen = false;
    },

    onCashbookMenuSelect(section) {
        if (section) {
            this.menuService.selectMenu(section);
        }
    },

    goCashbookHome() {
        const app = this.menuService.getCurrentApp();
        if (app) {
            this.menuService.selectMenu(app);
        }
    },
});

NavBar.template = "cashbook.NavBar";
NavBar.components = {
    ...NavBar.components,
    ErrorHandler,
    CashbookGlobalSearch,
    CashbookQuickCreate,
    CashbookMobileMenu,
};
