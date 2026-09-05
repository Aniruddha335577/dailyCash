/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useBus } from "@web/core/utils/hooks";
import { useEffect, useState } from "@odoo/owl";
import { CashbookSidebar } from "../sidebar/sidebar";
import { isCashbookApp } from "../utils/shell_utils";

patch(WebClient.prototype, {
    setup() {
        super.setup(...arguments);
        this.cbShellRevision = useState({ n: 0 });

        const bumpShell = () => {
            this.cbShellRevision.n++;
        };
        useBus(this.env.bus, "MENUS:APP-CHANGED", bumpShell);
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", bumpShell);
        useBus(this.env.bus, "WEB_CLIENT_READY", bumpShell);

        useEffect(
            () => {
                document.body.classList.toggle("cb_cashbook_shell", this.useCashbookShell);
                return () => document.body.classList.remove("cb_cashbook_shell");
            },
            () => [this.cbShellRevision.n, this.state.fullscreen]
        );
    },

    get useCashbookShell() {
        this.cbShellRevision.n;
        return isCashbookApp(this.menuService) && !this.state.fullscreen;
    },
});

WebClient.template = "cashbook.WebClient";
WebClient.components = {
    ...WebClient.components,
    CashbookSidebar,
};
