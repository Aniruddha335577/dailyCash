/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class CashbookQuickCreate extends Component {
    static template = "cashbook.QuickCreate";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.action = useService("action");
    }

    newEntry() {
        this.action.doAction("cashbook.action_cashbook_entry_ui");
    }

    newPartner() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.partner",
            views: [[false, "form"]],
            target: "current",
        });
    }

    newBook() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "cashbook.book",
            views: [[false, "form"]],
            target: "current",
        });
    }
}
