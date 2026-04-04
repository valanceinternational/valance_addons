/** @odoo-module **/
/**
 * login_restriction/static/src/js/session_watchdog.js
 *
 * Polls the server every 60 s.
 * If the server returns session_expired (because the HTTP hook or cron
 * killed the session during restricted hours) → show red banner + redirect.
 *
 * No user logins are hardcoded here. The server decides who is restricted.
 */

import { registry } from "@web/core/registry";
import { session } from "@web/session";

const POLL_INTERVAL_MS = 60_000;

function showForcedLogoutBanner(message) {
    document.getElementById("lr-force-logout-banner")?.remove();

    const banner = document.createElement("div");
    banner.id = "lr-force-logout-banner";
    Object.assign(banner.style, {
        position:   "fixed",
        top:        "0",
        left:       "0",
        width:      "100%",
        zIndex:     "999999",
        background: "#c0392b",
        color:      "#fff",
        fontFamily: "sans-serif",
        fontSize:   "16px",
        fontWeight: "bold",
        padding:    "18px 24px",
        textAlign:  "center",
        boxShadow:  "0 2px 8px rgba(0,0,0,0.4)",
    });

    const icon = document.createElement("span");
    icon.textContent = "🔒  ";
    banner.appendChild(icon);
    banner.appendChild(document.createTextNode(message + "  Redirecting to login…"));
    document.body.appendChild(banner);
}

async function checkSession() {
    try {
        const resp = await fetch("/web/dataset/call_kw", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method:  "call",
                id:      Date.now(),
                params: {
                    model:  "res.users",
                    method: "get_login_restriction_info",
                    args:   [],
                    kwargs: {},
                },
            }),
        });

        const data = await resp.json();

        // Session was killed by the server
        if (
            data?.error?.data?.exception_type === "session_expired" ||
            data?.error?.data?.name === "odoo.exceptions.SessionExpired"
        ) {
            const msg =
                data.error.data.message ||
                "Your session has been terminated due to login time restrictions.";
            showForcedLogoutBanner(msg);
            setTimeout(() => { window.location.href = "/web/login"; }, 3000);
            return;
        }

        // Server says restriction is active now — preemptively warn
        if (data?.result?.is_restricted_now) {
            const msg =
                data.result.message ||
                "Login is not allowed during restricted hours. You will be logged out shortly.";
            showForcedLogoutBanner(msg);
            setTimeout(() => { window.location.href = "/web/login"; }, 5000);
        }

    } catch (_e) {
        // Network error — skip silently, retry next poll
    }
}

// Start watchdog for all users (server decides restriction per group)
// First check after 55 s, then every 60 s
setTimeout(() => {
    checkSession();
    setInterval(checkSession, POLL_INTERVAL_MS);
}, 55_000);
