/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { ErrorHandler } from "@web/core/utils/components";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { CashbookGlobalSearch } from "../global_search/global_search";
import { CashbookQuickCreate } from "../quick_create/quick_create";
import { CashbookMobileMenu } from "../mobile_menu/mobile_menu";
import { isCashbookApp } from "../utils/shell_utils";

const ALLOWED_SYSTRAY_KEYS = new Set(["web.user_menu"]);

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.cbState = useState({
            mobileMenuOpen: false,
        });
    },

    get useCashbookShell() {
        const result = isCashbookApp(this.menuService);
        // #region agent log
        fetch('http://127.0.0.1:7245/ingest/426c4ef8-177a-40cf-aa0d-43be0692a04e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'577a85'},body:JSON.stringify({sessionId:'577a85',location:'navbar.js:useCashbookShell',message:'navbar shell check',data:{result,envIsSmall:this.env.isSmall},timestamp:Date.now(),hypothesisId:'A,B'})}).catch(()=>{});
        // #endregion
        return result;
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
