/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Transition } from "@web/core/transition";
import { BRAND_LOGO_URL, BRAND_NAME } from "../../utils/brand";
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

    setup() {
        this.brandName = BRAND_NAME;
        this.brandLogoUrl = BRAND_LOGO_URL;
    }

    getIcon(menu) {
        return getMenuIcon(menu);
    }

    onMenuClick(section) {
        this.props.onSelectMenu(section);
        this.props.onClose();
    }
}
