/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export function pruneSelection(selectedIds, visibleRecords) {
    const visible = new Set(visibleRecords.map((record) => record.id));
    return selectedIds.filter((id) => visible.has(id));
}

export function selectedCount(selectedIds) {
    return selectedIds.length;
}

export function isRecordSelected(selectedIds, recordId) {
    return selectedIds.includes(recordId);
}

export function allRecordsSelected(selectedIds, visibleRecords) {
    return (
        visibleRecords.length > 0 &&
        visibleRecords.every((record) => selectedIds.includes(record.id))
    );
}

export function toggleRecordSelection(selectedIds, recordId, ev) {
    ev.stopPropagation();
    if (isRecordSelected(selectedIds, recordId)) {
        return selectedIds.filter((id) => id !== recordId);
    }
    return [...selectedIds, recordId];
}

export function toggleAllVisibleSelection(selectedIds, visibleRecords, ev) {
    ev.stopPropagation();
    if (allRecordsSelected(selectedIds, visibleRecords)) {
        const visibleIds = new Set(visibleRecords.map((record) => record.id));
        return selectedIds.filter((id) => !visibleIds.has(id));
    }
    return [...new Set([...selectedIds, ...visibleRecords.map((record) => record.id)])];
}

export function confirmDeleteSelected({
    dialog,
    orm,
    model,
    selectedIds,
    recordLabel,
    onDeleted,
}) {
    if (!selectedIds.length) {
        return;
    }
    const count = selectedIds.length;
    dialog.add(ConfirmationDialog, {
        title: _t("Delete records"),
        body:
            count === 1
                ? _t("Are you sure you want to delete this %s?", recordLabel)
                : _t("Are you sure you want to delete these %s %s records?", count, recordLabel),
        confirm: async () => {
            await orm.unlink(model, [...selectedIds]);
            await onDeleted?.();
        },
        confirmLabel: _t("Delete"),
        cancel: () => {},
    });
}
