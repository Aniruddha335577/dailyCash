/** @odoo-module **/

export function aggregateEntryStats(entries, fieldName) {
    const stats = {};
    for (const entry of entries) {
        const rel = entry[fieldName];
        if (!rel) {
            continue;
        }
        const id = rel[0];
        if (!stats[id]) {
            stats[id] = { count: 0, total: 0, paid: 0, due: 0, currencyId: entry.currency_id?.[0] };
        }
        stats[id].count += 1;
        stats[id].total += entry.total_amount || 0;
        stats[id].paid += entry.paid || 0;
        stats[id].due += entry.due || 0;
        if (entry.currency_id) {
            stats[id].currencyId = entry.currency_id[0];
        }
    }
    return stats;
}

export function aggregatePaymentStats(payments, fieldName = "payment_method_id") {
    const stats = {};
    for (const payment of payments) {
        const rel = payment[fieldName];
        if (!rel) {
            continue;
        }
        const id = rel[0];
        if (!stats[id]) {
            stats[id] = { count: 0, total: 0 };
        }
        stats[id].count += 1;
        stats[id].total += payment.amount || 0;
    }
    return stats;
}

export function aggregateBookCounts(books) {
    const counts = {};
    for (const book of books) {
        const rel = book.business_id;
        if (!rel) {
            continue;
        }
        const id = rel[0];
        counts[id] = (counts[id] || 0) + 1;
    }
    return counts;
}
