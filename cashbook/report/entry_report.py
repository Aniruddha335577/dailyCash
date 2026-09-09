from odoo import models


class ReportCashbookEntry(models.AbstractModel):
    _name = "report.cashbook.report_entry"
    _description = "CashBook Entry Invoice Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env["cashbook.entry"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "cashbook.entry",
            "docs": docs,
        }
