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
import {
    directionClass,
    directionLabel,
    entrySettlementLabels,
    settlementLabels,
} from "../../utils/direction_labels";

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
                direction: ctx.default_direction || "all",
                paymentStatus: "all",
                dateFrom: "",
                dateTo: "",
                search: ctx.default_search || "",
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
            domain.push(["partner_id.partner_type", "=", "customer"]);
        } else if (f.partnerScope === "vendor") {
            domain.push(["partner_id.partner_type", "=", "vendor"]);
        }
        if (f.direction === "in" || f.direction === "out") {
            domain.push(["direction", "=", f.direction]);
        }
        if (f.dateFrom) {
            domain.push(["entry_datetime", ">=", `${f.dateFrom} 00:00:00`]);
        }
        if (f.dateTo) {
            domain.push(["entry_datetime", "<=", `${f.dateTo} 23:59:59`]);
        }
        if (f.search.trim()) {
            const term = f.search.trim();
            domain.push(
                "|",
                "|",
                ["name", "ilike", term],
                ["remarks", "ilike", term],
                ["partner_id.name", "ilike", term]
            );
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
            "name",
            "entry_datetime",
            "direction",
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

    setDirection(direction) {
        this.state.filters.direction = direction;
        this.onFilterChange();
    }

    get summaryLabels() {
        return settlementLabels(this.state.filters.direction);
    }

    directionLabel(direction) {
        return directionLabel(direction);
    }

    directionClass(direction) {
        return directionClass(direction);
    }

    get hasActiveFilters() {
        const f = this.state.filters;
        return Boolean(
            f.search.trim() ||
                f.bookId ||
                f.businessId ||
                f.entryTypeId ||
                f.partnerId ||
                f.paymentMethodId ||
                f.dateFrom ||
                f.dateTo ||
                f.partnerScope !== "all" ||
                f.direction !== "all" ||
                f.paymentStatus !== "all"
        );
    }

    async clearFilters() {
        this.state.filters = {
            bookId: "",
            businessId: "",
            entryTypeId: "",
            partnerId: "",
            paymentMethodId: "",
            partnerScope: "all",
            direction: "all",
            paymentStatus: "all",
            dateFrom: "",
            dateTo: "",
            search: "",
        };
        await this.loadEntries();
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
        const labels = entrySettlementLabels(entry.direction);
        if (!entry.paid) {
            return { label: labels.statusNone, class: "cb-badge-unpaid" };
        }
        if (!entry.due) {
            return { label: labels.statusComplete, class: "cb-badge-paid" };
        }
        return { label: labels.statusPartial, class: "cb-badge-partial" };
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
