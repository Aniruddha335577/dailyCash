/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { formatMonetary } from "@web/views/fields/formatters";
import { aggregateEntryStats } from "../../utils/entry_stats";

export class CashbookBookList extends Component {
    static template = "cashbook.BookList";
    static components = { Layout };
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const ctx = this.props.action.context || {};

        this.state = useState({
            books: [],
            businesses: [],
            stats: {},
            loading: true,
            search: "",
            businessId: ctx.default_business_id ? String(ctx.default_business_id) : "",
        });

        this.display = {
            controlPanel: {},
            searchPanel: false,
        };

        onWillStart(async () => {
            await this.loadBooks();
        });
    }

    get filteredBooks() {
        let list = this.state.books;
        if (this.state.businessId) {
            const businessId = parseInt(this.state.businessId, 10);
            list = list.filter(
                (book) => book.business_id && book.business_id[0] === businessId
            );
        }
        const term = this.state.search.trim().toLowerCase();
        if (!term) {
            return list;
        }
        return list.filter((book) => {
            const business = book.business_id ? book.business_id[1] : "";
            const description = book.description || "";
            return (
                book.name.toLowerCase().includes(term) ||
                business.toLowerCase().includes(term) ||
                description.toLowerCase().includes(term)
            );
        });
    }

    async loadBooks() {
        this.state.loading = true;
        const [books, businesses, entries] = await Promise.all([
            this.orm.searchRead(
                "cashbook.book",
                [["active", "=", true]],
                ["name", "business_id", "currency_id", "description"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.business",
                [["active", "=", true]],
                ["id", "name"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.entry",
                [],
                ["book_id", "total_amount", "paid", "due"],
                { limit: false }
            ),
        ]);
        this.state.books = books;
        this.state.businesses = businesses;
        this.state.stats = aggregateEntryStats(entries, "book_id");
        this.state.loading = false;
    }

    bookStats(book) {
        return this.state.stats[book.id] || { count: 0, total: 0, paid: 0, due: 0 };
    }

    formatMoney(amount, currencyId) {
        return formatMonetary(amount || 0, { currencyId });
    }

    openBook(book) {
        this.action.doAction("cashbook.action_cashbook_entry_ui", {
            additionalContext: { default_book_id: book.id },
        });
    }

    createBook() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.book",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openClassicList() {
        this.action.doAction("cashbook.action_cashbook_book");
    }
}

registry.category("actions").add("cashbook_book_list", CashbookBookList);
