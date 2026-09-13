/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { formatMonetary } from "@web/views/fields/formatters";
import {
    aggregateBookCounts,
    aggregateEntryStats,
} from "../../utils/entry_stats";

export class CashbookBusinessList extends Component {
    static template = "cashbook.BusinessList";
    static components = { Layout };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            businesses: [],
            entryStats: {},
            bookCounts: {},
            loading: true,
            search: "",
            viewMode: "grid",
        });

        this.display = {
            controlPanel: {},
            searchPanel: false,
        };

        onWillStart(async () => {
            await this.loadBusinesses();
        });
    }

    get filteredBusinesses() {
        const term = this.state.search.trim().toLowerCase();
        if (!term) {
            return this.state.businesses;
        }
        return this.state.businesses.filter((business) => {
            const currency = business.currency_id ? business.currency_id[1] : "";
            return (
                business.name.toLowerCase().includes(term) ||
                currency.toLowerCase().includes(term)
            );
        });
    }

    async loadBusinesses() {
        this.state.loading = true;
        const [businesses, entries, books] = await Promise.all([
            this.orm.searchRead(
                "cashbook.business",
                [["active", "=", true]],
                ["name", "currency_id"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.entry",
                [],
                ["business_id", "total_amount", "paid", "due", "currency_id"],
                { limit: false }
            ),
            this.orm.searchRead(
                "cashbook.book",
                [["active", "=", true]],
                ["business_id"],
                { limit: false }
            ),
        ]);
        this.state.businesses = businesses;
        this.state.entryStats = aggregateEntryStats(entries, "business_id");
        this.state.bookCounts = aggregateBookCounts(books);
        this.state.loading = false;
    }

    businessStats(business) {
        return this.state.entryStats[business.id] || {
            count: 0,
            total: 0,
            paid: 0,
            due: 0,
            currencyId: business.currency_id?.[0],
        };
    }

    bookCount(business) {
        return this.state.bookCounts[business.id] || 0;
    }

    formatMoney(amount, currencyId) {
        return formatMonetary(amount || 0, { currencyId });
    }

    setViewMode(mode) {
        this.state.viewMode = mode;
    }

    openBusiness(business) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.business",
            res_id: business.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    createBusiness() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.business",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openClassicList() {
        this.action.doAction("cashbook.action_cashbook_business");
    }
}

registry.category("actions").add("cashbook_business_list", CashbookBusinessList);
