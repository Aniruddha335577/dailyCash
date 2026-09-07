/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

export const DIRECTION_OPTIONS = [
    { value: "in", label: _t("Cash In") },
    { value: "out", label: _t("Cash Out") },
];

export function directionLabel(direction) {
    return direction === "out" ? _t("Cash Out") : _t("Cash In");
}

export function directionClass(direction) {
    return direction === "out" ? "cb-direction-out" : "cb-direction-in";
}

/** Labels for settled/outstanding amounts — meaning depends on entry direction. */
export function settlementLabels(directionFilter = "all") {
    if (directionFilter === "in") {
        return {
            settled: _t("Received"),
            outstanding: _t("To Receive"),
        };
    }
    if (directionFilter === "out") {
        return {
            settled: _t("Paid"),
            outstanding: _t("To Pay"),
        };
    }
    return {
        settled: _t("Settled"),
        outstanding: _t("Outstanding"),
    };
}

export function entrySettlementLabels(direction) {
    if (direction === "out") {
        return {
            settled: _t("Paid"),
            outstanding: _t("To Pay"),
            paymentsSection: _t("Payments"),
            addPayment: _t("Add payment"),
            statusComplete: _t("Paid"),
            statusPartial: _t("Partially paid"),
            statusNone: _t("Unpaid"),
            noPaymentsHint: _t("No payments yet — amount is fully to pay."),
        };
    }
    return {
        settled: _t("Received"),
        outstanding: _t("To Receive"),
        paymentsSection: _t("Receipts"),
        addPayment: _t("Add receipt"),
        statusComplete: _t("Received"),
        statusPartial: _t("Partially received"),
        statusNone: _t("Unreceived"),
        noPaymentsHint: _t("No receipts yet — amount is fully to receive."),
    };
}

export function partnerTypeLabel(partnerType) {
    if (partnerType === "vendor") {
        return _t("Vendor");
    }
    if (partnerType === "customer") {
        return _t("Customer");
    }
    return partnerType || "";
}
