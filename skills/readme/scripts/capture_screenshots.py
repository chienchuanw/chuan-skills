#!/usr/bin/env python3
"""
capture_screenshots.py -- Automatically capture screenshots of a web project.

Detects the dev server command, starts it, waits for it to be ready,
then captures screenshots of specified pages using Playwright.

Usage:
    python capture_screenshots.py [project_root] [assets_file]

Arguments:
    project_root  Path to the project (default: current directory)
    assets_file   Path to a JSON file listing pages to capture (optional)

If no assets_file is provided, captures a single screenshot of the root URL.

JSON format:
[
  {
    "filename": "dashboard.png",
    "description": "Main dashboard with sample data loaded",
    "type": "screenshot",
    "url_or_context": "/dashboard"
  },
  {
    "filename": "setup-flow.gif",
    "description": "Walkthrough of the initial setup wizard",
    "type": "screenshot",
    "url_or_context": "/setup"
  }
]

The url_or_context field can be a path (e.g., "/dashboard") or a full URL.
Paths are resolved relative to the detected dev server URL.

Requirements:
    pip install playwright && playwright install chromium
"""

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Dev server detection
# ---------------------------------------------------------------------------

DEV_SERVER_PATTERNS = [
    # (file, key/command, port hint)
    # Node.js / Next.js / Vite / etc.
    ("package.json", "dev"),
    ("package.json", "start"),
    ("package.json", "serve"),
    # Python
    ("pyproject.toml", None),
    ("manage.py", None),
    ("app.py", None),
    # Ruby
    ("Gemfile", None),
    # Go
    ("go.mod", None),
]

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


def _detect_from_package_json(pkg_json: Path) -> tuple[str, int] | None:
    """Extract dev server command and port from package.json."""
    try:
        data = json.loads(pkg_json.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    scripts = data.get("scripts", {})

    # Try common script names in priority order
    for script_name in ["dev", "start", "serve"]:
        if script_name in scripts:
            cmd = f"npm run {script_name}"
            port = _guess_port_from_script(scripts[script_name], data)
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


def _detect_from_pyproject(pyproject: Path) -> tuple[str, int] | None:
    """Detect dev server from pyproject.toml."""
    content = pyproject.read_text()

    if "uvicorn" in content:
        # Try to find the app module
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
    """Check if a port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
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

    # Wait for the port to become available
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

        if is_port_open(port):
            # Give the server a moment to finish initialization
            time.sleep(1)
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
        # Send SIGTERM to the entire process group
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
        context = browser.new_context(
            viewport={"width": viewport[0], "height": viewport[1]},
            device_scale_factor=2,  # Retina-quality screenshots
        )
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
                page.goto(url, wait_until="networkidle", timeout=15000)
                # Wait a bit for any animations to settle
                page.wait_for_timeout(500)
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
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    assets_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

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

        if is_port_open(port):
            print(f"Dev server already running on port {port}")
            server_already_running = True
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
            if is_port_open(port):
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
        results = capture_screenshots(base_url, assets, output_dir)
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

    # Write results to JSON for downstream use
    results_path = output_dir / "capture_results.json"
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
