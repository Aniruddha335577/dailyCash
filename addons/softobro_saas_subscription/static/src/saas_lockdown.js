/** @odoo-module **/

import { actionService } from "@web/webclient/actions/action_service";
import { registry } from "@web/core/registry";
import { router } from "@web/core/browser/router";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";

const BLOCKED_PATHS = new Set(session.saas_blocked_paths || ["apps", "settings", "discuss"]);
const BLOCKED_ACTION_FRAGMENTS = [
    "open_module_tree",
    "action_general_configuration",
    "action_discuss",
    "mail.action_discuss",
];
const BLOCKED_MENU_XMLIDS = new Set([
    "base.menu_management",
    "base.menu_administration",
    "base.menu_tests",
    "mail.menu_root_discuss",
]);

function platformLocked() {
    return Boolean(session.saas_platform_locked);
}

function actionBlocked(actionName) {
    if (!platformLocked() || !actionName) {
        return false;
    }
    const name = String(actionName);
    if (BLOCKED_PATHS.has(name)) {
        return true;
    }
    return BLOCKED_ACTION_FRAGMENTS.some((fragment) => name.includes(fragment));
}

function routeActionBlocked(state) {
    if (!platformLocked()) {
        return false;
    }
    const action = state?.action || state?.actionStack?.at(-1)?.action;
    return actionBlocked(action);
}

function actionRequestBlocked(actionRequest) {
    if (!platformLocked()) {
        return false;
    }
    if (typeof actionRequest === "string") {
        return actionBlocked(actionRequest);
    }
    if (typeof actionRequest === "object" && actionRequest) {
        if (actionRequest.path && actionBlocked(actionRequest.path)) {
            return true;
        }
        if (actionRequest.xml_id && BLOCKED_MENU_XMLIDS.has(actionRequest.xml_id)) {
            return true;
        }
        if (actionRequest.tag === "mail.action_discuss") {
            return true;
        }
    }
    return false;
}

function blockedNotice(env) {
    env.services.notification.add(
        _t("This area is reserved for platform support staff."),
        { type: "warning" }
    );
}

function safeHomeState() {
    const homeUrl = session.saas_home_url || "/odoo";
    if (homeUrl.includes("menu_id=")) {
        const menuId = homeUrl.split("menu_id=")[1];
        return { menu_id: Number(menuId), action: null, actionStack: [] };
    }
    return { action: null, actionStack: [] };
}

patch(actionService, {
    start(env) {
        const service = super.start(...arguments);

        const superLoadState = service.loadState.bind(service);
        service.loadState = async (state = router.current) => {
            if (routeActionBlocked(state)) {
                blockedNotice(env);
                const safeState = safeHomeState();
                router.pushState(safeState, { replace: true });
                return superLoadState(safeState);
            }
            return superLoadState(state);
        };

        const superDoAction = service.doAction.bind(service);
        service.doAction = async (actionRequest, options = {}) => {
            if (actionRequestBlocked(actionRequest)) {
                blockedNotice(env);
                return;
            }
            return superDoAction(actionRequest, options);
        };

        return service;
    },
});

const commandProviderRegistry = registry.category("command_provider");
const menuProvider = commandProviderRegistry.get("menu");
if (menuProvider) {
    const superProvide = menuProvider.provide.bind(menuProvider);
    menuProvider.provide = async (env, options) => {
        const commands = await superProvide(env, options);
        if (!platformLocked()) {
            return commands;
        }
        return commands.filter((command) => {
            const href = command.href || "";
            const name = command.name || "";
            if ([...BLOCKED_PATHS].some((path) => href.includes(path))) {
                return false;
            }
            if (/Discuss|Apps|Settings|Tests/i.test(name)) {
                return false;
            }
            return true;
        });
    };
}
