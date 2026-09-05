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
        // #region agent log
        fetch('http://127.0.0.1:7245/ingest/426c4ef8-177a-40cf-aa0d-43be0692a04e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'577a85'},body:JSON.stringify({sessionId:'577a85',location:'webclient.js:setup',message:'WebClient setup',data:{initialShell:this.useCashbookShell,webClientTemplate:WebClient.template},timestamp:Date.now(),runId:'post-fix',hypothesisId:'A'})}).catch(()=>{});
        // #endregion

        const bumpShell = () => {
            this.cbShellRevision.n++;
            // #region agent log
            fetch('http://127.0.0.1:7245/ingest/426c4ef8-177a-40cf-aa0d-43be0692a04e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'577a85'},body:JSON.stringify({sessionId:'577a85',location:'webclient.js:bumpShell',message:'shell revision bumped',data:{revision:this.cbShellRevision.n,useCashbookShell:this.useCashbookShell},timestamp:Date.now(),runId:'post-fix',hypothesisId:'A'})}).catch(()=>{});
            // #endregion
        };
        useBus(this.env.bus, "MENUS:APP-CHANGED", bumpShell);
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", bumpShell);
        useBus(this.env.bus, "WEB_CLIENT_READY", bumpShell);

        useEffect(
            () => {
                document.body.classList.toggle("cb_cashbook_shell", this.useCashbookShell);
                const sidebar = document.querySelector(".cb_sidebar");
                const shellLayout = document.querySelector(".cb_shell_layout");
                const avatar = document.querySelector(".cb_navbar .o_user_avatar");
                const navbarEl = document.querySelector(".cb_main_navbar");
                const avatarStyles = avatar ? getComputedStyle(avatar) : null;
                const navbarStyles = navbarEl ? getComputedStyle(navbarEl) : null;
                // #region agent log
                fetch('http://127.0.0.1:7245/ingest/426c4ef8-177a-40cf-aa0d-43be0692a04e',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'577a85'},body:JSON.stringify({sessionId:'577a85',location:'webclient.js:useEffect',message:'shell DOM snapshot',data:{useCashbookShell:this.useCashbookShell,revision:this.cbShellRevision.n,fullscreen:this.state.fullscreen,envIsSmall:this.env.isSmall,sidebarInDom:!!sidebar,shellLayoutInDom:!!shellLayout,sectionCount:sidebar?sidebar.querySelectorAll('.cb_sidebar_item').length:0,avatarHeight:avatarStyles?.height,avatarWidth:avatarStyles?.width,avatarTop:avatar?.getBoundingClientRect?.().top,navbarHeightVar:navbarStyles?.getPropertyValue('--o-navbar-height')},timestamp:Date.now(),runId:'post-fix',hypothesisId:'B,D,E'})}).catch(()=>{});
                // #endregion
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
