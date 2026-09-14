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
import {
    allRecordsSelected,
    confirmDeleteSelected,
    isRecordSelected,
    pruneSelection,
    selectedCount,
    toggleAllVisibleSelection,
    toggleRecordSelection,
} from "../../utils/record_selection";

const SECTION_CONFIG = {
    entry_types: {
        selectionKey: "entryTypes",
        model: "cashbook.entry.type",
        label: "entry type",
    },
    payment_methods: {
        selectionKey: "paymentMethods",
        model: "cashbook.payment.method",
        label: "payment method",
    },
    report_templates: {
        selectionKey: "reportTemplates",
        model: "cashbook.report.template",
        label: "report template",
    },
};

export class CashbookConfigurationList extends Component {
    static template = "cashbook.ConfigurationList";
    static components = { Layout };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");

        const ctx = this.props.action.context || {};
        this.section = ctx.default_section || "all";

        this.state = useState({
            entryTypes: [],
            paymentMethods: [],
            reportTemplates: [],
            entryTypeStats: {},
            paymentStats: {},
            loading: true,
            search: "",
            viewMode: "grid",
            selection: {
                entryTypes: [],
                paymentMethods: [],
                reportTemplates: [],
            },
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

    get showReportTemplates() {
        return this.section === "all" || this.section === "report_templates";
    }

    get pageTitle() {
        if (this.section === "entry_types") {
            return _t("Entry Types");
        }
        if (this.section === "payment_methods") {
            return _t("Payment Methods");
        }
        if (this.section === "report_templates") {
            return _t("Report Templates");
        }
        return _t("Configuration");
    }

    get filteredEntryTypes() {
        return this._filterRecords(this.state.entryTypes, ["name", "description"]);
    }

    get filteredPaymentMethods() {
        return this._filterRecords(this.state.paymentMethods, ["name", "description"]);
    }

    get filteredReportTemplates() {
        return this._filterRecords(this.state.reportTemplates, ["name", "layout"]);
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
        const loads = [
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
                "cashbook.report.template",
                [["active", "=", true]],
                ["name", "layout", "page_size", "is_default"],
                { order: "sequence, name" }
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
        ];
        const [entryTypes, paymentMethods, reportTemplates, entries, payments] =
            await Promise.all(loads);
        this.state.entryTypes = entryTypes;
        this.state.paymentMethods = paymentMethods;
        this.state.reportTemplates = reportTemplates;
        this.state.entryTypeStats = aggregateEntryStats(entries, "entry_type_id");
        this.state.paymentStats = aggregatePaymentStats(payments);
        this.state.selection.entryTypes = pruneSelection(
            this.state.selection.entryTypes,
            this.filteredEntryTypes
        );
        this.state.selection.paymentMethods = pruneSelection(
            this.state.selection.paymentMethods,
            this.filteredPaymentMethods
        );
        this.state.selection.reportTemplates = pruneSelection(
            this.state.selection.reportTemplates,
            this.filteredReportTemplates
        );
        this.state.loading = false;
    }

    _sectionRecords(section) {
        if (section === "entry_types") {
            return this.filteredEntryTypes;
        }
        if (section === "payment_methods") {
            return this.filteredPaymentMethods;
        }
        return this.filteredReportTemplates;
    }

    _sectionSelection(section) {
        return this.state.selection[SECTION_CONFIG[section].selectionKey];
    }

    sectionSelectedCount(section) {
        return selectedCount(this._sectionSelection(section));
    }

    allSectionSelected(section) {
        return allRecordsSelected(this._sectionSelection(section), this._sectionRecords(section));
    }

    isSectionSelected(section, recordId) {
        return isRecordSelected(this._sectionSelection(section), recordId);
    }

    toggleSectionRecord(section, recordId, ev) {
        const key = SECTION_CONFIG[section].selectionKey;
        this.state.selection[key] = toggleRecordSelection(
            this.state.selection[key],
            recordId,
            ev
        );
    }

    toggleSectionSelectAll(section, ev) {
        const key = SECTION_CONFIG[section].selectionKey;
        this.state.selection[key] = toggleAllVisibleSelection(
            this.state.selection[key],
            this._sectionRecords(section),
            ev
        );
    }

    setViewMode(mode) {
        if (mode === "grid") {
            this.state.selection.entryTypes = [];
            this.state.selection.paymentMethods = [];
            this.state.selection.reportTemplates = [];
        }
        this.state.viewMode = mode;
    }

    deleteSectionSelected(section) {
        const config = SECTION_CONFIG[section];
        confirmDeleteSelected({
            dialog: this.dialog,
            orm: this.orm,
            model: config.model,
            selectedIds: this._sectionSelection(section),
            recordLabel: config.label,
            onDeleted: async () => {
                this.state.selection[config.selectionKey] = [];
                await this.loadConfiguration();
            },
        });
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

    layoutLabel(layout) {
        const labels = {
            simple: _t("Simple"),
            classic: _t("Classic"),
            modern: _t("Modern"),
        };
        return labels[layout] || layout;
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

    openReportTemplate(template) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.report.template",
            res_id: template.id,
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

    createReportTemplate() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.report.template",
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

    openClassicReportTemplates() {
        this.action.doAction("cashbook.action_cashbook_report_template");
    }
}

registry.category("actions").add("cashbook_configuration_list", CashbookConfigurationList);
