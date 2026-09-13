from odoo import fields, models
from odoo.tools.misc import format_datetime

from .entry_report import _get_saas_logo_data_uri


def _chunk_lines(lines, size=4):
    if not lines:
        return []
    return [lines[index : index + size] for index in range(0, len(lines), size)]


class ReportCashbookEntryList(models.AbstractModel):
    _name = "report.cashbook.report_entry_list"
    _description = "CashBook Entry List Report"

    def _format_bucket_amounts(self, docs, bucket):
        sample = docs.filtered(lambda entry: entry.currency_id == bucket["currency"])[:1]
        if not sample:
            sample = docs[:1]
        if not sample:
            return bucket
        entry = sample[0]
        bucket["total_label"] = entry.format_report_amount(bucket["total"])
        bucket["paid_label"] = entry.format_report_amount(bucket["paid"])
        bucket["due_label"] = entry.format_report_amount(bucket["due"])
        return bucket

    def _get_report_values(self, docids, data=None):
        docs = self.env["cashbook.entry"].browse(docids).sorted(
            key=lambda entry: (entry.entry_datetime, entry.id),
            reverse=True,
        )
        filter_lines = self.env.context.get("report_filter_summary") or []
        filter_line_rows = _chunk_lines(filter_lines, 4)
        report_business = False
        currency_totals = []
        if docs:
            businesses = docs.mapped("business_id")
            report_business = businesses[0] if len(businesses) == 1 else False
            currency_totals = self.env["cashbook.entry"].get_list_report_currency_totals(docs)
            currency_totals = [
                self._format_bucket_amounts(docs, bucket) for bucket in currency_totals
            ]
        return {
            "doc_ids": docids,
            "doc_model": "cashbook.entry",
            "docs": docs,
            "filter_lines": filter_lines,
            "filter_line_rows": filter_line_rows,
            "filters_applied": bool(filter_lines),
            "currency_totals": currency_totals,
            "report_business": report_business,
            "report_generated_at_label": format_datetime(
                self.env, fields.Datetime.now()
            ),
            "saas_logo_data_uri": _get_saas_logo_data_uri(),
            "powered_by_label": "Powered by HisabBro",
            "saas_product_label": "HisabBro",
        }
