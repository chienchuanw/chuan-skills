#!/usr/bin/env python3
"""
capture_screenshots.py -- Automatically capture screenshots of a web project.

Detects the dev server command, starts it, waits for it to be ready,
then captures screenshots of specified pages using Playwright.

Usage:
    python capture_screenshots.py [project_root] [assets_file] [options]

Arguments:
    project_root  Path to the project (default: current directory)
    assets_file   Path to a JSON file listing pages to capture (optional)

Options:
    --viewport WIDTHxHEIGHT   Screenshot viewport (default: 1280x720)
    --timeout MS              Navigation timeout in ms (default: 60000)
    --delay SECONDS           Post-render delay in seconds (default: 3.0)
    --wait-until STRATEGY     Playwright wait strategy (default: domcontentloaded)
    --storage-state PATH      Playwright storage state JSON for auth sessions
    --results-path PATH       Where to write capture_results.json (default: /tmp/)
    --no-results              Skip writing capture_results.json

JSON format for assets_file:
[
  {
    "filename": "dashboard.png",
    "description": "Main dashboard with sample data loaded",
    "type": "screenshot",
    "url_or_context": "/dashboard"
  }
]

The url_or_context field can be a path (e.g., "/dashboard") or a full URL.
Paths are resolved relative to the detected dev server URL.

Requirements:
    pip install playwright && playwright install chromium
"""

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Literal


# ---------------------------------------------------------------------------
# Dev server detection
# ---------------------------------------------------------------------------

DEFAULT_PORTS = {
    "next": 3000,
    "vite": 5173,
    "react-scripts": 3000,
    "vue-cli-service": 8080,
    "nuxt": 3000,
    "webpack-dev-server": 8080,
    "flask": 5000,
    "django": 8000,
    "uvicorn": 8000,
    "rails": 3000,
}


def detect_dev_server(project_root: Path) -> tuple[str, int] | None:
    """Detect the dev server command and port from project files.

    Returns (command, port) or None if detection fails.
    """
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        result = _detect_from_package_json(pkg_json)
        if result:
            return result

    # Python: Django
    manage_py = project_root / "manage.py"
    if manage_py.exists():
        return ("python manage.py runserver", 8000)

    # Python: Flask / generic
    app_py = project_root / "app.py"
    if app_py.exists():
        return ("flask run", 5000)

    # Python: pyproject.toml with uvicorn/flask
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        result = _detect_from_pyproject(pyproject)
        if result:
            return result

    # Ruby on Rails
    gemfile = project_root / "Gemfile"
    if gemfile.exists() and (project_root / "config" / "routes.rb").exists():
        return ("rails server", 3000)

    return None


def _detect_package_manager(project_root: Path) -> str:
    """Detect npm/yarn/pnpm from lock files."""
    if (project_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _detect_from_package_json(pkg_json: Path) -> tuple[str, int] | None:
    """Extract dev server command and port from package.json."""
    try:
        data = json.loads(pkg_json.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    scripts = data.get("scripts", {})
    project_root = pkg_json.parent
    pkg_manager = _detect_package_manager(project_root)

    # Priority 1: exact matches
    for script_name in ["dev", "start", "serve"]:
        if script_name in scripts:
            cmd = f"{pkg_manager} run {script_name}"
            port = _guess_port_from_script(scripts[script_name], data)
            return (cmd, port)

    # Priority 2: prefixed variants (dev:web, dev:frontend, start:app, etc.)
    for prefix in ["dev:", "start:", "serve:"]:
        for script_name, script_cmd in scripts.items():
            if script_name.startswith(prefix):
                # If it delegates to a workspace, try to follow it for port detection
                delegated = _follow_workspace_delegation(
                    script_cmd, project_root, data
                )
                if delegated:
                    return delegated
                cmd = f"{pkg_manager} run {script_name}"
                port = _guess_port_from_script(script_cmd, data)
                return (cmd, port)

    return None


def _guess_port_from_script(script_cmd: str, pkg_data: dict) -> int:
    """Guess the port from a script command string."""
    # Check for explicit port flags
    port_match = re.search(r"(?:--port|-p)\s+(\d+)", script_cmd)
    if port_match:
        return int(port_match.group(1))

    port_match = re.search(r"PORT=(\d+)", script_cmd)
    if port_match:
        return int(port_match.group(1))

    # Check for known tools in the script command
    for tool, default_port in DEFAULT_PORTS.items():
        if tool in script_cmd:
            return default_port

    # Check dependencies for framework hints
    all_deps = {}
    all_deps.update(pkg_data.get("dependencies", {}))
    all_deps.update(pkg_data.get("devDependencies", {}))

    for dep in all_deps:
        if dep in ("next", "nuxt"):
            return DEFAULT_PORTS.get(dep, 3000)
        if dep == "vite":
            return 5173

    return 3000  # Default fallback for Node.js


def _follow_workspace_delegation(
    script_cmd: str, project_root: Path, root_pkg_data: dict
) -> tuple[str, int] | None:
    """Follow pnpm/yarn workspace filter delegation to find the actual command."""
    # Match: pnpm --filter <package> <script>
    filter_match = re.search(r"pnpm\s+--filter\s+(\S+)\s+(\w+)", script_cmd)
    if not filter_match:
        return None

    pkg_name = filter_match.group(1)
    script_name = filter_match.group(2)

    # Find the workspace package directory
    workspace_dir = _find_workspace_package(project_root, pkg_name)
    if not workspace_dir:
        return None

    ws_pkg_json = workspace_dir / "package.json"
    if not ws_pkg_json.exists():
        return None

    try:
        ws_data = json.loads(ws_pkg_json.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    ws_scripts = ws_data.get("scripts", {})
    if script_name in ws_scripts:
        port = _guess_port_from_script(ws_scripts[script_name], ws_data)
        # Run from root using the original command
        cmd = f"pnpm --filter {pkg_name} {script_name}"
        return (cmd, port)

    return None


def _find_workspace_package(project_root: Path, pkg_name: str) -> Path | None:
    """Find a workspace package directory by name."""
    for ws_dir in ["packages", "apps", "libs", "services"]:
        ws_path = project_root / ws_dir
        if not ws_path.is_dir():
            continue
        for child in ws_path.iterdir():
            if not child.is_dir():
                continue
            child_pkg = child / "package.json"
            if child_pkg.exists():
                try:
                    child_data = json.loads(child_pkg.read_text())
                    if child_data.get("name") == pkg_name:
                        return child
                except (json.JSONDecodeError, OSError):
                    continue
    return None


def _detect_from_pyproject(pyproject: Path) -> tuple[str, int] | None:
    """Detect dev server from pyproject.toml."""
    content = pyproject.read_text()

    if "uvicorn" in content:
        app_match = re.search(r'(\w+\.app)', content)
        module = app_match.group(1) if app_match else "main:app"
        return (f"uvicorn {module} --reload", 8000)

    if "flask" in content:
        return ("flask run", 5000)

    if "django" in content:
        return ("python manage.py runserver", 8000)

    return None


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def is_port_open(port: int, host: str = "localhost") -> bool:
    """Fast TCP check -- does something listen on this port?"""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def is_server_ready(port: int, host: str = "localhost") -> bool:
    """HTTP-level check -- is the server actually responding to requests?

    A process can bind a port before it is ready to serve HTTP. This function
    sends a real GET request and accepts any response with status < 500,
    including 401/403 (which mean the server is up but requires auth).
    """
    try:
        url = f"http://{host}:{port}/"
        req = urllib.request.Request(url, method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        return resp.status < 500
    except urllib.error.HTTPError as e:
        # 4xx responses (including 401/403) mean the server is up
        return e.code < 500
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def start_dev_server(
    command: str, port: int, project_root: Path, timeout: int = 60
) -> subprocess.Popen:
    """Start the dev server and wait until it is ready.

    Returns the Popen process object.
    Raises TimeoutError if the server does not start within the timeout.
    """
    env = os.environ.copy()
    env["BROWSER"] = "none"  # Prevent auto-opening browser
    env["PORT"] = str(port)  # Some frameworks respect this

    print(f"Starting dev server: {command}")
    print(f"Expected port: {port}")

    proc = subprocess.Popen(
        command,
        shell=True,
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,  # Create process group for clean shutdown
    )

    # Wait for the server to be ready (HTTP-level, not just TCP)
    start_time = time.time()
    while time.time() - start_time < timeout:
        if proc.poll() is not None:
            stdout = proc.stdout.read().decode() if proc.stdout else ""
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            raise RuntimeError(
                f"Dev server exited with code {proc.returncode}.\n"
                f"stdout: {stdout[:500]}\n"
                f"stderr: {stderr[:500]}"
            )

        if is_port_open(port) and is_server_ready(port):
            print(f"Dev server is ready on port {port}")
            return proc

        time.sleep(0.5)

    # Timeout -- clean up
    stop_server(proc)
    raise TimeoutError(
        f"Dev server did not start within {timeout}s on port {port}. "
        f"Command: {command}"
    )


def stop_server(proc: subprocess.Popen) -> None:
    """Gracefully stop the dev server process group."""
    if proc.poll() is not None:
        return

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except (ProcessLookupError, ChildProcessError):
        pass
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait(timeout=3)
        except (ProcessLookupError, ChildProcessError):
            pass


# ---------------------------------------------------------------------------
# Screenshot capture
# ---------------------------------------------------------------------------

def capture_screenshots(
    base_url: str,
    assets: list[dict],
    output_dir: Path,
    viewport: tuple[int, int] = (1280, 720),
    full_page: bool = True,
    wait_strategy: Literal["commit", "domcontentloaded", "load", "networkidle"] = "domcontentloaded",
    post_render_delay: float = 3.0,
    nav_timeout: int = 60000,
    storage_state: str | None = None,
) -> list[dict]:
    """Capture screenshots using Playwright.

    Returns a list of dicts with filename, path, and status.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Playwright is not installed. Install it with:\n"
            "  pip install playwright && playwright install chromium\n"
        )
        return [{"filename": a["filename"], "status": "skipped", "reason": "playwright not installed"} for a in assets]

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context_kwargs = {
            "viewport": {"width": viewport[0], "height": viewport[1]},
            "device_scale_factor": 2,  # Retina-quality screenshots
        }
        if storage_state:
            context_kwargs["storage_state"] = storage_state

        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        for asset in assets:
            filename = asset["filename"]
            url_or_path = asset.get("url_or_context", "/")

            # Resolve relative paths against base URL
            if url_or_path.startswith("/"):
                url = f"{base_url.rstrip('/')}{url_or_path}"
            elif url_or_path.startswith("http"):
                url = url_or_path
            else:
                url = f"{base_url.rstrip('/')}/{url_or_path}"

            output_path = output_dir / filename

            try:
                print(f"Capturing: {url} -> {output_path}")
                page.goto(url, wait_until=wait_strategy, timeout=nav_timeout)
                # Wait for rendering to settle (animations, lazy loading, etc.)
                page.wait_for_timeout(int(post_render_delay * 1000))
                page.screenshot(path=str(output_path), full_page=full_page)
                results.append({
                    "filename": filename,
                    "path": str(output_path),
                    "status": "captured",
                })
                print(f"  Saved: {output_path}")
            except Exception as e:
                results.append({
                    "filename": filename,
                    "status": "failed",
                    "reason": str(e),
                })
                print(f"  Failed: {e}")

        browser.close()

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Capture screenshots of a web project automatically."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the project (default: current directory)",
    )
    parser.add_argument(
        "assets_file",
        nargs="?",
        default=None,
        help="Path to a JSON file listing pages to capture",
    )
    parser.add_argument(
        "--viewport",
        default="1280x720",
        help="Viewport size as WIDTHxHEIGHT (default: 1280x720)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60000,
        help="Navigation timeout in milliseconds (default: 60000)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Post-render delay in seconds (default: 3.0)",
    )
    parser.add_argument(
        "--wait-until",
        default="domcontentloaded",
        choices=["domcontentloaded", "load", "networkidle", "commit"],
        help="Playwright wait strategy (default: domcontentloaded)",
    )
    parser.add_argument(
        "--storage-state",
        default=None,
        help="Path to Playwright storage state JSON for authenticated sessions",
    )
    parser.add_argument(
        "--results-path",
        default=None,
        help="Path to write capture_results.json (default: /tmp/capture_results.json)",
    )
    parser.add_argument(
        "--no-results",
        action="store_true",
        help="Do not write capture_results.json",
    )

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    assets_file = Path(args.assets_file) if args.assets_file else None

    # Parse viewport
    try:
        w, h = args.viewport.split("x")
        viewport = (int(w), int(h))
    except ValueError:
        print(f"Invalid viewport format: {args.viewport}. Use WIDTHxHEIGHT (e.g., 1280x720).")
        sys.exit(1)

    # Load asset list
    if assets_file and assets_file.exists():
        with open(assets_file) as f:
            assets = json.load(f)
        # Filter to screenshot type only (skip gifs for now)
        assets = [a for a in assets if a.get("type") in ("screenshot", None)]
    else:
        # Default: capture the root page
        assets = [
            {
                "filename": "overview.png",
                "description": "Application overview",
                "type": "screenshot",
                "url_or_context": "/",
            }
        ]

    if not assets:
        print("No screenshots to capture.")
        return

    output_dir = project_root / "assets" / "screenshots"

    # Detect dev server
    detection = detect_dev_server(project_root)
    server_already_running = False
    proc = None

    if detection:
        command, port = detection

        if is_port_open(port) and is_server_ready(port):
            print(f"Dev server already running on port {port}")
            server_already_running = True
        elif is_port_open(port):
            print(f"Port {port} is bound but not responding to HTTP. It may be stale.")
            print("Attempting to start a fresh dev server...")
            try:
                proc = start_dev_server(command, port, project_root)
            except (RuntimeError, TimeoutError) as e:
                print(f"Error starting dev server: {e}")
                print("Falling back to asset checklist.")
                _run_checklist_fallback(project_root, assets_file)
                return
        else:
            try:
                proc = start_dev_server(command, port, project_root)
            except (RuntimeError, TimeoutError) as e:
                print(f"Error starting dev server: {e}")
                print("Falling back to asset checklist.")
                _run_checklist_fallback(project_root, assets_file)
                return
    else:
        # Check common ports in case something is already running
        for port in [3000, 5173, 8080, 5000, 8000]:
            if is_port_open(port) and is_server_ready(port):
                print(f"Found running server on port {port}")
                server_already_running = True
                break
        else:
            print("Could not detect dev server and no server is running.")
            print("Falling back to asset checklist.")
            _run_checklist_fallback(project_root, assets_file)
            return

    base_url = f"http://localhost:{port}"

    try:
        results = capture_screenshots(
            base_url,
            assets,
            output_dir,
            viewport=viewport,
            wait_strategy=args.wait_until,
            post_render_delay=args.delay,
            nav_timeout=args.timeout,
            storage_state=args.storage_state,
        )
    finally:
        if proc and not server_already_running:
            print("Stopping dev server...")
            stop_server(proc)

    # Summary
    print("\n==========================================")
    print(" Screenshot Capture Summary")
    print("==========================================\n")

    captured = [r for r in results if r["status"] == "captured"]
    failed = [r for r in results if r["status"] != "captured"]

    if captured:
        print(f"Captured {len(captured)} screenshot(s):")
        for r in captured:
            print(f"  - {r['path']}")

    if failed:
        print(f"\nFailed/skipped {len(failed)} screenshot(s):")
        for r in failed:
            print(f"  - {r['filename']}: {r.get('reason', 'unknown')}")

    # Write results JSON (to /tmp/ by default, not the project directory)
    if not args.no_results:
        if args.results_path:
            results_path = Path(args.results_path)
        else:
            results_path = Path(tempfile.gettempdir()) / "capture_results.json"
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_path}")


def _run_checklist_fallback(project_root: Path, assets_file: Path | None):
    """Fall back to the checklist script when capture fails."""
    script_dir = Path(__file__).parent
    checklist_script = script_dir / "prepare_assets.sh"

    if checklist_script.exists():
        args = ["bash", str(checklist_script), str(project_root)]
        if assets_file:
            args.append(str(assets_file))
        subprocess.run(args)
    else:
        print("Checklist script not found. Please capture screenshots manually.")


if __name__ == "__main__":
    main()
