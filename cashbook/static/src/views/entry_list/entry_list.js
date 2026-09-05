/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { deserializeDateTime, toLocaleDateTimeString } from "@web/core/l10n/dates";
import { formatMonetary } from "@web/views/fields/formatters";
import { QuickEntryPanel } from "../../components/quick_entry_panel/quick_entry_panel";

export class CashbookEntryList extends Component {
    static template = "cashbook.EntryList";
    static components = { Layout, QuickEntryPanel };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const ctx = this.props.action.context || {};

        this.state = useState({
            entries: [],
            books: [],
            businesses: [],
            entryTypes: [],
            partners: [],
            paymentMethods: [],
            loading: true,
            summary: { total: 0, paid: 0, due: 0 },
            filters: {
                bookId: ctx.default_book_id ? String(ctx.default_book_id) : "",
                businessId: ctx.default_business_id ? String(ctx.default_business_id) : "",
                entryTypeId: ctx.default_entry_type_id ? String(ctx.default_entry_type_id) : "",
                partnerId: ctx.default_partner_id ? String(ctx.default_partner_id) : "",
                paymentMethodId: ctx.default_payment_method_id
                    ? String(ctx.default_payment_method_id)
                    : "",
                partnerScope: ctx.default_partner_scope || "all",
                paymentStatus: "all",
                dateFrom: "",
                dateTo: "",
                search: "",
            },
            quickEntry: {
                open: false,
                entryId: null,
            },
        });

        this.display = {
            controlPanel: {},
            searchPanel: false,
        };

        onWillStart(async () => {
            await this.loadFilterOptions();
            await this.loadEntries();
        });
    }

    getDomain() {
        const domain = [];
        const f = this.state.filters;

        if (f.bookId) {
            domain.push(["book_id", "=", parseInt(f.bookId, 10)]);
        }
        if (f.businessId) {
            domain.push(["business_id", "=", parseInt(f.businessId, 10)]);
        }
        if (f.entryTypeId) {
            domain.push(["entry_type_id", "=", parseInt(f.entryTypeId, 10)]);
        }
        if (f.partnerId) {
            domain.push(["partner_id", "=", parseInt(f.partnerId, 10)]);
        }
        if (f.paymentMethodId) {
            domain.push([
                "payment_ids.payment_method_id",
                "=",
                parseInt(f.paymentMethodId, 10),
            ]);
        }
        if (f.partnerScope === "customer") {
            domain.push(["partner_id.partner_type", "in", ["customer", "both"]]);
        } else if (f.partnerScope === "vendor") {
            domain.push(["partner_id.partner_type", "in", ["vendor", "both"]]);
        }
        if (f.dateFrom) {
            domain.push(["entry_datetime", ">=", `${f.dateFrom} 00:00:00`]);
        }
        if (f.dateTo) {
            domain.push(["entry_datetime", "<=", `${f.dateTo} 23:59:59`]);
        }
        if (f.search.trim()) {
            const term = f.search.trim();
            domain.push("|", ["remarks", "ilike", term], ["partner_id.name", "ilike", term]);
        }
        if (f.paymentStatus === "paid") {
            domain.push(["due", "=", 0], ["paid", ">", 0]);
        } else if (f.paymentStatus === "unpaid") {
            domain.push(["paid", "=", 0]);
        } else if (f.paymentStatus === "partial") {
            domain.push(["due", ">", 0], ["paid", ">", 0]);
        }
        return domain;
    }

    async loadFilterOptions() {
        const [books, businesses, entryTypes, partners, paymentMethods] = await Promise.all([
            this.orm.searchRead("cashbook.book", [], ["id", "name"], { order: "name" }),
            this.orm.searchRead("cashbook.business", [["active", "=", true]], ["id", "name"], {
                order: "name",
            }),
            this.orm.searchRead("cashbook.entry.type", [], ["id", "name"], { order: "name" }),
            this.orm.searchRead("cashbook.partner", [["active", "=", true]], ["id", "name"], {
                order: "name",
            }),
            this.orm.searchRead(
                "cashbook.payment.method",
                [["active", "=", true]],
                ["id", "name"],
                { order: "name" }
            ),
        ]);
        this.state.books = books;
        this.state.businesses = businesses;
        this.state.entryTypes = entryTypes;
        this.state.partners = partners;
        this.state.paymentMethods = paymentMethods;
    }

    async loadEntries() {
        this.state.loading = true;
        const domain = this.getDomain();
        const fields = [
            "entry_datetime",
            "book_id",
            "entry_type_id",
            "partner_id",
            "total_amount",
            "paid",
            "due",
            "currency_id",
            "remarks",
        ];
        this.state.entries = await this.orm.searchRead(
            "cashbook.entry",
            domain,
            fields,
            { order: "entry_datetime desc, id desc", limit: 500 }
        );
        this.state.summary = this.state.entries.reduce(
            (acc, entry) => {
                acc.total += entry.total_amount || 0;
                acc.paid += entry.paid || 0;
                acc.due += entry.due || 0;
                return acc;
            },
            { total: 0, paid: 0, due: 0 }
        );
        this.state.loading = false;
    }

    async onFilterChange() {
        await this.loadEntries();
    }

    async onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            await this.loadEntries();
        }
    }

    setPartnerScope(scope) {
        this.state.filters.partnerScope = scope;
        this.onFilterChange();
    }

    setPaymentStatus(status) {
        this.state.filters.paymentStatus = status;
        this.onFilterChange();
    }

    formatMoney(amount, currencyId) {
        return formatMonetary(amount || 0, { currencyId });
    }

    formatDate(value) {
        if (!value) {
            return "";
        }
        return toLocaleDateTimeString(deserializeDateTime(value));
    }

    paymentStatus(entry) {
        if (!entry.paid) {
            return { label: _t("Unpaid"), class: "cb-badge-unpaid" };
        }
        if (!entry.due) {
            return { label: _t("Paid"), class: "cb-badge-paid" };
        }
        return { label: _t("Partial"), class: "cb-badge-partial" };
    }

    openEntry(entry) {
        this.state.quickEntry = { open: true, entryId: entry.id };
    }

    openQuickEntry(entryId = null) {
        this.state.quickEntry = { open: true, entryId };
    }

    closeQuickEntry() {
        this.state.quickEntry = { open: false, entryId: null };
    }

    async onQuickEntrySaved() {
        this.closeQuickEntry();
        await this.loadEntries();
    }

    createEntry() {
        this.openQuickEntry(null);
    }

    openClassicList() {
        this.action.doAction("cashbook.action_cashbook_entry");
    }
}

registry.category("actions").add("cashbook_entry_list", CashbookEntryList);
