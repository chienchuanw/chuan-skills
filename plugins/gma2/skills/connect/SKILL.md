---
name: connect
description: >
  Install, register, and verify the gma2 MCP server so Claude can drive a grandMA2
  lighting console (or onPC) over Telnet. Use this whenever the user wants to
  "connect to grandMA2", "set up the MA2 console", "install gma2 mcp", "hook up
  the lighting desk", asks why the gma2 tools aren't available, or is about to run
  any other gma2 skill (presets / setlist / bpm) and the server isn't connected
  yet. This is the entry point for the whole gma2 plugin — run it first.
---

# gma2 connect

Register the **gma2** MCP server with Claude Code, point it at the console, and
confirm the link is live by reading back the patch. Every other gma2 skill
(`presets`, `setlist`, `bpm`) assumes this server is connected.

## What you need from the user

- **Console IP** (`GMA_HOST`) — the address of the machine running grandMA2 / onPC,
  reachable on the network (e.g. an Ethernet link). Required.
- **User / password** — default `administrator` / `admin`. Ask only if non-default.
- **Path to the `gma2-mcp` repo** — the MCP server's code. Required to register it.
  Ask if you don't already know it (commonly `~/Documents/gma2-mcp`).

## Steps

1. **Register the server** (replace the IP and repo path):

   ```bash
   claude mcp add gma2 \
     -e GMA_HOST=<IP> -e GMA_USER=administrator -e GMA_PASSWORD=admin \
     -- uv --directory <path-to-gma2-mcp> run python -m src.server
   ```

   To re-point an existing registration, `claude mcp remove gma2` first.

2. **Confirm registration**: `claude mcp get gma2` should show **✔ Connected**.
   This only means the server *process* speaks the protocol — not that the Telnet
   link to the console is up (that happens lazily on the first real command).

3. **Heads-up the user about the next-session rule**: a freshly added MCP server's
   tools (the `mcp__gma2__*` tools) load on the **next** Claude Code session, not
   the current one. So you usually can't call them in the same session you added
   them. Tell the user to start a new session, then verify with a real command.

4. **Verify the console link** (next session, or as a fallback now): ask Claude to
   run a harmless read like "list the groups" / "list fixtures 1 thru 60", or use
   the `send_raw_command` tool with `List Group`. Getting real patch data back is
   the true proof the Telnet link works.

## Reading the patch (recommended)

Map the rig before doing anything else — other skills need the Fixture IDs. Query
`List Fixture 1 Thru 1000` and `List Group`. This tells you which fixture types are
patched and at which IDs (e.g. `frame` = Fine 600L at 101–109).

**Read-back gotcha:** this console's Telnet truncates long replies if read too
fast. Use a generous read delay (≈1.5 s) and reasonable timeout, and prefer
`List Fixture 1 Thru 1000` in one shot over many small ranges.

## Troubleshooting

- **First command fails / no patch** — Telnet not enabled on the onPC (Setup →
  Network), wrong IP, or user/password mismatch. Port 30000 is the command port;
  30001 is read-only log output.
- **`Fix` and "current page" are per-user** — the server logs in as `Administrator`,
  but the operator usually runs as a *different* user. Show data (sequences,
  macros, pages, views, executor assignments, button functions) is global and
  shared; only **executor Fix** and the **current page** are user-scoped. So a
  `Fix` issued over this connection only affects Administrator's pages — the
  operator must fix on their own user. Correct syntax here is `Fix Executor x.y`
  (a toggle); do not add `On`.
