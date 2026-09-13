/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";

export class CashbookGlobalSearch extends Component {
    static template = "cashbook.GlobalSearch";
    static props = {};

    setup() {
        this.action = useService("action");
        this.state = useState({ query: "" });
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            this.submitSearch();
        }
    }

    submitSearch() {
        const term = this.state.query.trim();
        this.action.doAction("cashbook.action_cashbook_entry_ui", {
            additionalContext: term ? { default_search: term } : {},
        });
    }
}
