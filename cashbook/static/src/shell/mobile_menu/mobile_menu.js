/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Transition } from "@web/core/transition";
import { getMenuIcon } from "../utils/shell_utils";

export class CashbookMobileMenu extends Component {
    static template = "cashbook.MobileMenu";
    static components = { Transition };
    static props = {
        open: Boolean,
        sections: Array,
        onClose: Function,
        onSelectMenu: Function,
    };

    getIcon(menu) {
        return getMenuIcon(menu);
    }

    onMenuClick(section) {
        this.props.onSelectMenu(section);
        this.props.onClose();
    }
}
