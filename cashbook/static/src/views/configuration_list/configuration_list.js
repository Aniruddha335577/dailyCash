/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { formatMonetary } from "@web/views/fields/formatters";
import {
    aggregateEntryStats,
    aggregatePaymentStats,
} from "../../utils/entry_stats";

export class CashbookConfigurationList extends Component {
    static template = "cashbook.ConfigurationList";
    static components = { Layout };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const ctx = this.props.action.context || {};
        this.section = ctx.default_section || "all";

        this.state = useState({
            entryTypes: [],
            paymentMethods: [],
            entryTypeStats: {},
            paymentStats: {},
            loading: true,
            search: "",
        });

        this.display = {
            controlPanel: {},
            searchPanel: false,
        };

        onWillStart(async () => {
            await this.loadConfiguration();
        });
    }

    get showEntryTypes() {
        return this.section === "all" || this.section === "entry_types";
    }

    get showPaymentMethods() {
        return this.section === "all" || this.section === "payment_methods";
    }

    get pageTitle() {
        if (this.section === "entry_types") {
            return _t("Entry Types");
        }
        if (this.section === "payment_methods") {
            return _t("Payment Methods");
        }
        return _t("Configuration");
    }

    get filteredEntryTypes() {
        return this._filterRecords(this.state.entryTypes, ["name", "description"]);
    }

    get filteredPaymentMethods() {
        return this._filterRecords(this.state.paymentMethods, ["name", "description"]);
    }

    _filterRecords(records, fields) {
        const term = this.state.search.trim().toLowerCase();
        if (!term) {
            return records;
        }
        return records.filter((record) =>
            fields.some((field) => (record[field] || "").toLowerCase().includes(term))
        );
    }

    async loadConfiguration() {
        this.state.loading = true;
        const [entryTypes, paymentMethods, entries, payments] = await Promise.all([
            this.orm.searchRead(
                "cashbook.entry.type",
                [["active", "=", true]],
                ["name", "description"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.payment.method",
                [["active", "=", true]],
                ["name", "description"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.entry",
                [],
                ["entry_type_id", "total_amount", "paid", "due", "currency_id"],
                { limit: false }
            ),
            this.orm.searchRead(
                "cashbook.payment",
                [],
                ["payment_method_id", "amount"],
                { limit: false }
            ),
        ]);
        this.state.entryTypes = entryTypes;
        this.state.paymentMethods = paymentMethods;
        this.state.entryTypeStats = aggregateEntryStats(entries, "entry_type_id");
        this.state.paymentStats = aggregatePaymentStats(payments);
        this.state.loading = false;
    }

    entryTypeStats(entryType) {
        return this.state.entryTypeStats[entryType.id] || {
            count: 0,
            total: 0,
            paid: 0,
            due: 0,
            currencyId: null,
        };
    }

    paymentMethodStats(paymentMethod) {
        return this.state.paymentStats[paymentMethod.id] || { count: 0, total: 0 };
    }

    formatMoney(amount, currencyId) {
        return formatMonetary(amount || 0, { currencyId });
    }

    openEntryType(entryType) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.entry.type",
            res_id: entryType.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openPaymentMethod(paymentMethod) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.payment.method",
            res_id: paymentMethod.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    createEntryType() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.entry.type",
            views: [[false, "form"]],
            target: "current",
        });
    }

    createPaymentMethod() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.payment.method",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openClassicEntryTypes() {
        this.action.doAction("cashbook.action_cashbook_entry_type");
    }

    openClassicPaymentMethods() {
        this.action.doAction("cashbook.action_cashbook_payment_method");
    }
}

registry.category("actions").add("cashbook_configuration_list", CashbookConfigurationList);
