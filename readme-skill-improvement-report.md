# `/readme` Skill -- Screenshot Capture Improvement Report

## Context

While running the `/readme` skill on a pnpm monorepo (Next.js + Electron), the automatic screenshot capture step failed on every attempt. Manual intervention was required to get screenshots captured. This report documents the root causes, workarounds used, and suggested improvements.

## Issues Encountered

### 1. Playwright not pre-installed

The capture script depends on Playwright, but it is not installed by default. When missing, the script silently falls back to the manual checklist -- defeating the purpose of automatic capture.

**What happened:** The script printed install instructions and produced zero screenshots.

**Workaround:** Manually ran `pip install playwright && playwright install chromium` before re-running.

### 2. `networkidle` wait strategy is too aggressive

The `capture_screenshots()` function uses `wait_until="networkidle"` when navigating to pages. Next.js dev servers (and similar frameworks) keep long-lived connections open (HMR WebSocket, polling), which means `networkidle` never resolves.

**What happened:** All three page navigations timed out at the 15-second limit.

**Workaround:** Wrote a custom Playwright script using `wait_until="domcontentloaded"` with an explicit `wait_for_timeout(3000)` to let the page render.

### 3. Default timeout too short (15 seconds)

Next.js dev servers compile pages on first request. A cold start can easily take 10--30 seconds for the initial compilation, especially in monorepo setups with shared packages. The 15-second timeout in `page.goto()` is not enough.

**What happened:** Even after switching to `domcontentloaded`, the first attempt still timed out at 15s because the server was compiling.

**Workaround:** Increased timeout to 60 seconds.

### 4. Monorepo dev server detection fails

The `detect_dev_server()` function reads the root `package.json` and looks for `dev`, `start`, or `serve` scripts. In this project, the root `dev:web` script is `pnpm --filter @vocab-hero/web dev`, which delegates to the workspace package. The detection function:

- Finds the `dev:web` script but does not recognize it as a standard dev command (it looks for `dev`, not `dev:web`).
- Falls back to scanning common ports, which may or may not find a running server.

**What happened:** The script did not detect the dev server command, so it could not start one automatically. It only worked because a server was already running on port 3000.

### 5. Stale/hung dev server process

The existing dev server on port 3000 was accepting TCP connections (socket connect succeeded) but not responding to HTTP requests. This made `is_port_open()` return `True` even though the server was unusable.

**What happened:** The script detected "server already running" but every page navigation timed out. Had to `kill -9` the process and restart the server manually.

### 6. Artifact left behind

The script writes a `capture_results.json` file to `assets/screenshots/`. This metadata file is not useful to the project and should not be committed.

**What happened:** Had to manually delete `assets/screenshots/capture_results.json` after capture.

---

## Gotchas

Things to be aware of when using the screenshot capture feature:

1. **Playwright requires one-time setup.** Run `pip install playwright && playwright install chromium` before first use. The `chromium` browser download is ~150 MB and takes a separate step after pip install.

2. **`networkidle` does not work with HMR.** Any dev server that maintains a WebSocket or long-polling connection (Next.js, Vite, Nuxt, Webpack Dev Server) will never reach "network idle." Always use `domcontentloaded` or `load` instead.

3. **Cold-start compilation can be slow.** The first request to a Next.js/Vite dev server triggers on-demand compilation. Budget at least 30--60 seconds for the first page, not 15.

4. **Port open does not mean server ready.** A Node.js process can bind a port before it is ready to serve HTTP requests. Use an HTTP health check (e.g., `curl`) instead of a raw TCP socket check.

5. **Monorepo `scripts` field uses non-standard names.** Projects commonly use `dev:web`, `dev:api`, `start:frontend`, etc. The detection logic only checks `dev`, `start`, and `serve`.

6. **pnpm/yarn workspace delegation is opaque.** A root script like `pnpm --filter @vocab-hero/web dev` does not tell you the actual command being run. You need to read the workspace package's `package.json` to determine the framework and port.

7. **Auth-gated pages produce blank or login screenshots.** If the app requires authentication, Playwright will capture a login redirect instead of the actual page. The script has no mechanism to handle login flows.

8. **`capture_results.json` should be cleaned up.** The script writes this artifact into the project's `assets/screenshots/` directory. Either write it to a temp directory or delete it after use.

---

## Suggested Improvements

### capture_screenshots.py

| Area                    | Current Behavior                                     | Suggested Change                                                                                                                        |
| ----------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Wait strategy           | `wait_until="networkidle"`                           | Default to `"domcontentloaded"` with configurable `post_render_delay` (default 3s)                                                      |
| Navigation timeout      | 15 seconds, hardcoded                                | 60 seconds default, configurable via `--timeout` flag or JSON field                                                                     |
| HTTP readiness check    | TCP socket check (`is_port_open`)                    | HTTP `GET /` with status code check (200, 301, 302, 307)                                                                                |
| Monorepo support        | Only reads root `package.json` `dev`/`start`/`serve` | Scan workspace packages; support `dev:*` pattern; follow `pnpm --filter` delegation                                                     |
| Playwright auto-install | Prints instructions and gives up                     | Offer to run `pip install playwright && playwright install chromium` automatically, or check at script start with a clear error message |
| Results file            | Writes `capture_results.json` in project assets      | Write to `/tmp/` or accept `--results-path` flag; do not pollute the project directory                                                  |
| Auth handling           | None                                                 | Accept optional `--cookie` or `--storage-state` flag for authenticated sessions                                                         |
| Viewport                | Hardcoded 1280x720                                   | Accept `--viewport` flag; default is fine but should be overridable                                                                     |

### Skill instructions (readme skill prompt)

- The skill should check for Playwright availability **before** writing the README, so it can decide upfront whether to include image placeholders or real paths.
- Add a retry mechanism: if the first capture attempt fails, restart the dev server and retry once before falling back to the manual checklist.
- For monorepos, the skill should identify the correct workspace package and run its dev server directly rather than relying on root-level scripts.
- Document the Playwright prerequisite prominently in the skill's own README or help text, not just as an afterthought when the script fails.

### generate_tree.sh

- No issues encountered. Works as expected.

### prepare_assets.sh (fallback)

- The fallback is reasonable but should be a last resort, not the default when Playwright is missing. The skill should try harder to install and use Playwright before giving up.
