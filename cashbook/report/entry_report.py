import base64
import os

from odoo import models
from odoo.modules.module import get_module_path


def _get_saas_logo_data_uri():
    module_path = get_module_path("cashbook")
    if not module_path:
        return False
    for filename in ("brand_logo.png", "brand_logo.svg"):
        path = os.path.join(module_path, "static", "img", filename)
        if os.path.isfile(path):
            mime = "image/png" if filename.endswith(".png") else "image/svg+xml"
            with open(path, "rb") as logo_file:
                encoded = base64.b64encode(logo_file.read()).decode()
            return f"data:{mime};base64,{encoded}"
    return False


class ReportCashbookEntry(models.AbstractModel):
    _name = "report.cashbook.report_entry"
    _description = "CashBook Entry Invoice Report"

    def _get_report_values(self, docids, data=None):
        docs = self.env["cashbook.entry"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "cashbook.entry",
            "docs": docs,
            "saas_logo_data_uri": _get_saas_logo_data_uri(),
            "powered_by_label": "Powered by SoftoBRo",
            "saas_product_label": "HisabBro",
        }
