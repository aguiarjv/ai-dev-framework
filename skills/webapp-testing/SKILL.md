---
name: webapp-testing
description: Exercise and debug a local web application in a browser, including UI behavior, screenshots, and browser errors. Use for browser-level checks, not API-only or unit tests.
license: Apache-2.0; see LICENSE.txt
---

# Web Application Testing

Use the project's existing test runner and browser tooling when they fit the
task. Otherwise use an available browser automation tool, such as Playwright.
The bundled Python helper is optional; it starts one or more local servers,
waits for their ports, runs a test command, and stops only the processes it
started. Resolve `scripts/with_server.py` relative to this `SKILL.md` and run
it with `--help` before using it. It does not install Playwright or a browser.
For example, pass `--server "npm run dev" --port 5173 -- <test-command>` when
that is the project's documented server command.

Test the smallest flow that answers the user's question. For a dynamic app,
start or connect to the local server, navigate, and wait for a meaningful page
condition (for example a visible heading or completed request) before
inspecting the rendered DOM. Do not depend on `networkidle` for apps that
poll, stream, or keep connections open. Prefer accessible roles, labels, and
stable test IDs over brittle positional selectors.

Inspect the page before acting on unfamiliar elements. Verify observable
outcomes rather than only clicks: changed content, navigation, validation,
network responses, or persisted state as applicable. Capture console or page
errors and a screenshot when useful for diagnosis. Check relevant viewport
sizes for visual work. Keep waits bounded and avoid fixed sleeps except when
diagnosing a timing problem.

Use only server commands appropriate for the project. Do not launch another
server on a port already in use. Close browser sessions, stop servers started
for the check, and report what was tested and what remains unverified.

Adapted from [Composio's webapp-testing skill](https://github.com/composio-community/awesome-codex-skills/tree/master/webapp-testing).
