/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { formatMonetary } from "@web/views/fields/formatters";
import { aggregateEntryStats } from "../../utils/entry_stats";
import { partnerTypeLabel } from "../../utils/direction_labels";

export class CashbookPartnerList extends Component {
    static template = "cashbook.PartnerList";
    static components = { Layout };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            partners: [],
            stats: {},
            loading: true,
            search: "",
            partnerType: "all",
            viewMode: "grid",
        });

        this.display = {
            controlPanel: {},
            searchPanel: false,
        };

        onWillStart(async () => {
            await this.loadPartners();
        });
    }

    get filteredPartners() {
        let list = this.state.partners;
        if (this.state.partnerType === "customer") {
            list = list.filter((p) => p.partner_type === "customer");
        } else if (this.state.partnerType === "vendor") {
            list = list.filter((p) => p.partner_type === "vendor");
        }
        const term = this.state.search.trim().toLowerCase();
        if (!term) {
            return list;
        }
        return list.filter((partner) => {
            const phone = partner.phone || "";
            const notes = partner.notes || "";
            return (
                partner.name.toLowerCase().includes(term) ||
                phone.toLowerCase().includes(term) ||
                notes.toLowerCase().includes(term)
            );
        });
    }

    async loadPartners() {
        this.state.loading = true;
        const [partners, entries] = await Promise.all([
            this.orm.searchRead(
                "cashbook.partner",
                [["active", "=", true]],
                ["name", "partner_type", "phone", "notes"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.entry",
                [],
                ["partner_id", "total_amount", "paid", "due", "currency_id"],
                { limit: false }
            ),
        ]);
        this.state.partners = partners;
        this.state.stats = aggregateEntryStats(entries, "partner_id");
        this.state.loading = false;
    }

    partnerStats(partner) {
        return this.state.stats[partner.id] || { count: 0, total: 0, paid: 0, due: 0, currencyId: null };
    }

    partnerTypeLabel(partnerType) {
        return partnerTypeLabel(partnerType);
    }

    partnerTypeClass(partnerType) {
        return `cb-type-${partnerType}`;
    }

    partnerIconClass(partnerType) {
        if (partnerType === "vendor") {
            return "cb-entity-icon-vendor";
        }
        return "cb-entity-icon-customer";
    }

    formatMoney(amount, currencyId) {
        return formatMonetary(amount || 0, { currencyId });
    }

    setPartnerType(partnerType) {
        this.state.partnerType = partnerType;
    }

    setViewMode(mode) {
        this.state.viewMode = mode;
    }

    openPartner(partner) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.partner",
            res_id: partner.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    createPartner() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.partner",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openClassicList() {
        this.action.doAction("cashbook.action_cashbook_partner");
    }
}

registry.category("actions").add("cashbook_partner_list", CashbookPartnerList);
