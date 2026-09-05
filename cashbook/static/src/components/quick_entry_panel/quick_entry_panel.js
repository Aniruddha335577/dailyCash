/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState } from "@odoo/owl";
import { serializeDateTime } from "@web/core/l10n/dates";
import { useService } from "@web/core/utils/hooks";
import { formatMonetary } from "@web/views/fields/formatters";

const { DateTime } = luxon;

function defaultLine() {
    return {
        id: null,
        product_name: "",
        product_price: 0,
        quantity: 1,
        uom: "",
        description: "",
        _deleted: false,
    };
}

function defaultPayment() {
    return {
        id: null,
        payment_method_id: "",
        amount: 0,
        payment_datetime: DateTime.now().toFormat("yyyy-MM-dd'T'HH:mm"),
        remarks: "",
        _deleted: false,
    };
}

function toDatetimeLocal(sqlValue) {
    if (!sqlValue) {
        return DateTime.now().toFormat("yyyy-MM-dd'T'HH:mm");
    }
    return DateTime.fromSQL(sqlValue, { zone: "utc" })
        .setZone("default")
        .toFormat("yyyy-MM-dd'T'HH:mm");
}

export class QuickEntryPanel extends Component {
    static template = "cashbook.QuickEntryPanel";
    static props = {
        entryId: { type: [Number, { value: null }], optional: true },
        books: { type: Array },
        entryTypes: { type: Array },
        defaultBookId: { type: String, optional: true },
        defaultPartnerId: { type: String, optional: true },
        defaultEntryTypeId: { type: String, optional: true },
        onClose: Function,
        onSaved: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            saving: false,
            partners: [],
            paymentMethods: [],
            currencyId: null,
            form: this._emptyForm(),
        });

        onWillStart(async () => {
            await this._loadOptions();
            if (this.props.entryId) {
                await this._loadEntry(this.props.entryId);
            } else {
                this._applyDefaults();
            }
            this.state.loading = false;
        });
    }

    get isEdit() {
        return Boolean(this.props.entryId);
    }

    get title() {
        return this.isEdit ? _t("Edit Entry") : _t("New Entry");
    }

    get activeLines() {
        return this.state.form.lines.filter((l) => !l._deleted);
    }

    get activePayments() {
        return this.state.form.payments.filter((p) => !p._deleted);
    }

    get lineTotal() {
        return this.activeLines.reduce(
            (sum, line) => sum + (line.product_price || 0) * (line.quantity || 0),
            0
        );
    }

    get paidTotal() {
        return this.activePayments.reduce((sum, p) => sum + (p.amount || 0), 0);
    }

    get dueTotal() {
        return this.lineTotal - this.paidTotal;
    }

    _emptyForm() {
        return {
            book_id: "",
            entry_type_id: "",
            partner_id: "",
            entry_datetime: DateTime.now().toFormat("yyyy-MM-dd'T'HH:mm"),
            remarks: "",
            lines: [defaultLine()],
            payments: [],
        };
    }

    _applyDefaults() {
        if (this.props.defaultBookId) {
            this.state.form.book_id = String(this.props.defaultBookId);
        } else if (this.props.books.length) {
            this.state.form.book_id = String(this.props.books[0].id);
        }
        if (this.props.defaultEntryTypeId) {
            this.state.form.entry_type_id = String(this.props.defaultEntryTypeId);
        } else if (this.props.entryTypes.length) {
            this.state.form.entry_type_id = String(this.props.entryTypes[0].id);
        }
        if (this.props.defaultPartnerId) {
            this.state.form.partner_id = String(this.props.defaultPartnerId);
        }
        this._updateCurrencyFromBook();
    }

    async _loadOptions() {
        const [partners, paymentMethods] = await Promise.all([
            this.orm.searchRead(
                "cashbook.partner",
                [["active", "=", true]],
                ["id", "name", "partner_type"],
                { order: "name" }
            ),
            this.orm.searchRead(
                "cashbook.payment.method",
                [["active", "=", true]],
                ["id", "name"],
                { order: "name" }
            ),
        ]);
        this.state.partners = partners;
        this.state.paymentMethods = paymentMethods;
    }

    async _loadEntry(entryId) {
        const [entry] = await this.orm.read(
            "cashbook.entry",
            [entryId],
            ["book_id", "entry_type_id", "partner_id", "entry_datetime", "remarks", "currency_id"]
        );
        const [lines, payments] = await Promise.all([
            this.orm.searchRead(
                "cashbook.entry.line",
                [["entry_id", "=", entryId]],
                ["product_name", "product_price", "quantity", "uom", "description"]
            ),
            this.orm.searchRead(
                "cashbook.payment",
                [["entry_id", "=", entryId]],
                ["payment_method_id", "amount", "payment_datetime", "remarks"]
            ),
        ]);

        this.state.currencyId = entry.currency_id ? entry.currency_id[0] : null;
        this.state.form = {
            book_id: entry.book_id ? String(entry.book_id[0]) : "",
            entry_type_id: entry.entry_type_id ? String(entry.entry_type_id[0]) : "",
            partner_id: entry.partner_id ? String(entry.partner_id[0]) : "",
            entry_datetime: toDatetimeLocal(entry.entry_datetime),
            remarks: entry.remarks || "",
            lines: lines.length
                ? lines.map((l) => ({
                      id: l.id,
                      product_name: l.product_name,
                      product_price: l.product_price,
                      quantity: l.quantity,
                      uom: l.uom || "",
                      description: l.description || "",
                      _deleted: false,
                  }))
                : [defaultLine()],
            payments: payments.map((p) => ({
                id: p.id,
                payment_method_id: p.payment_method_id ? String(p.payment_method_id[0]) : "",
                amount: p.amount,
                payment_datetime: toDatetimeLocal(p.payment_datetime),
                remarks: p.remarks || "",
                _deleted: false,
            })),
        };
    }

    async _updateCurrencyFromBook() {
        const bookId = parseInt(this.state.form.book_id, 10);
        if (!bookId) {
            this.state.currencyId = null;
            return;
        }
        const [book] = await this.orm.read("cashbook.book", [bookId], ["business_id"]);
        if (!book?.business_id) {
            return;
        }
        const [business] = await this.orm.read(
            "cashbook.business",
            [book.business_id[0]],
            ["currency_id"]
        );
        this.state.currencyId = business.currency_id ? business.currency_id[0] : null;
    }

    async onBookChange() {
        await this._updateCurrencyFromBook();
    }

    addLine() {
        this.state.form.lines.push(defaultLine());
    }

    removeLine(index) {
        const line = this.state.form.lines[index];
        if (line.id) {
            line._deleted = true;
        } else {
            this.state.form.lines.splice(index, 1);
        }
        if (!this.activeLines.length) {
            this.state.form.lines.push(defaultLine());
        }
    }

    addPayment() {
        const payment = defaultPayment();
        if (this.state.paymentMethods.length) {
            payment.payment_method_id = String(this.state.paymentMethods[0].id);
        }
        this.state.form.payments.push(payment);
    }

    removePayment(index) {
        const payment = this.state.form.payments[index];
        if (payment.id) {
            payment._deleted = true;
        } else {
            this.state.form.payments.splice(index, 1);
        }
    }

    formatMoney(amount) {
        return formatMonetary(amount || 0, { currencyId: this.state.currencyId });
    }

    _validate() {
        const f = this.state.form;
        if (!f.book_id) {
            return _t("Book is required.");
        }
        if (!f.entry_type_id) {
            return _t("Entry type is required.");
        }
        if (!this.activeLines.length) {
            return _t("Add at least one entry line.");
        }
        for (const line of this.activeLines) {
            if (!line.product_name?.trim()) {
                return _t("Each line needs an item name.");
            }
            if (line.quantity <= 0) {
                return _t("Line quantity must be greater than zero.");
            }
            if (line.product_price < 0) {
                return _t("Line price cannot be negative.");
            }
        }
        for (const payment of this.activePayments) {
            if (!payment.payment_method_id) {
                return _t("Select a payment method for each payment.");
            }
            if (payment.amount <= 0) {
                return _t("Payment amount must be greater than zero.");
            }
        }
        if (this.paidTotal > this.lineTotal) {
            return _t("Total payments cannot exceed entry total.");
        }
        return null;
    }

    _buildLineCommands() {
        const commands = [];
        for (const line of this.state.form.lines) {
            const vals = {
                product_name: line.product_name,
                product_price: line.product_price,
                quantity: line.quantity,
                uom: line.uom || false,
                description: line.description || false,
            };
            if (line._deleted && line.id) {
                commands.push([2, line.id]);
            } else if (line.id) {
                commands.push([1, line.id, vals]);
            } else if (!line._deleted) {
                commands.push([0, 0, vals]);
            }
        }
        return commands;
    }

    _buildPaymentCommands() {
        const commands = [];
        for (const payment of this.state.form.payments) {
            const dt = DateTime.fromISO(payment.payment_datetime, { zone: "default" });
            const vals = {
                payment_method_id: parseInt(payment.payment_method_id, 10),
                amount: payment.amount,
                payment_datetime: serializeDateTime(dt),
                remarks: payment.remarks || false,
            };
            if (payment._deleted && payment.id) {
                commands.push([2, payment.id]);
            } else if (payment.id) {
                commands.push([1, payment.id, vals]);
            } else if (!payment._deleted) {
                commands.push([0, 0, vals]);
            }
        }
        return commands;
    }

    _buildValues() {
        const f = this.state.form;
        const entryDt = DateTime.fromISO(f.entry_datetime, { zone: "default" });
        return {
            book_id: parseInt(f.book_id, 10),
            entry_type_id: parseInt(f.entry_type_id, 10),
            partner_id: f.partner_id ? parseInt(f.partner_id, 10) : false,
            entry_datetime: serializeDateTime(entryDt),
            remarks: f.remarks || false,
            line_ids: this._buildLineCommands(),
            payment_ids: this._buildPaymentCommands(),
        };
    }

    async save() {
        const error = this._validate();
        if (error) {
            this.notification.add(error, { type: "danger" });
            return;
        }
        this.state.saving = true;
        try {
            const vals = this._buildValues();
            if (this.isEdit) {
                await this.orm.write("cashbook.entry", [this.props.entryId], vals);
                this.notification.add(_t("Entry updated."), { type: "success" });
            } else {
                await this.orm.create("cashbook.entry", [vals]);
                this.notification.add(_t("Entry created."), { type: "success" });
            }
            this.props.onSaved();
        } catch (e) {
            this.notification.add(e.message || _t("Could not save entry."), { type: "danger" });
        } finally {
            this.state.saving = false;
        }
    }

    openFullForm() {
        if (this.isEdit) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: "cashbook.entry",
                res_id: this.props.entryId,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }

    close() {
        this.props.onClose();
    }
}
