"""Run all five submission routes against a disposable local Worker.

Requires the companion collector checkout and its npm dependencies. No cloud
account or deployment is needed. --public additionally opens a short-lived HTTPS
Quick Tunnel to this isolated receiver; use synthetic data only.
"""

import argparse
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from smoke_metascience import smoke

from benchside.infrastructure.http_sink import HttpExportSink

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ("gaps", "feedback", "usage", "surveys", "activity")


def available_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def public_check(endpoint, root, env, payloads, catalog, keep_alive_seconds):
    executable = shutil.which("cloudflared")
    if not executable:
        raise RuntimeError("Install cloudflared from Cloudflare before using --public")
    log_path = root / "tunnel.log"
    with log_path.open("w+") as log:
        tunnel = subprocess.Popen(
            [executable, "--no-autoupdate", "tunnel", "--protocol", "http2", "--url", endpoint],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=root,
            start_new_session=True,
        )
        try:
            # A newly allocated hostname can outlive a resolver's negative cache.
            deadline = time.monotonic() + 120
            public_url = None
            last_error = "Tunnel URL has not appeared"
            while time.monotonic() < deadline and tunnel.poll() is None:
                match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", log_path.read_text())
                if match:
                    if public_url is None:
                        public_url = match.group(0)
                        print(f"Verifying temporary HTTPS receiver: {public_url}", flush=True)
                    try:
                        with urlopen(public_url + "/v1/studies", timeout=5) as response:
                            served = json.load(response)
                        if served != catalog:
                            raise RuntimeError(
                                "Public URL does not match this isolated test receiver"
                            )
                        break
                    except (URLError, TimeoutError, OSError) as exc:
                        last_error = str(exc)
                time.sleep(1)
            else:
                raise RuntimeError(
                    f"Could not verify {public_url or 'the temporary HTTPS receiver'}: "
                    f"{last_error}\n" + log_path.read_text()[-2500:]
                )
            for channel, payload in payloads.items():
                data = json.loads(payload)
                if channel == "gaps":
                    for observation in data["observations"]:
                        observation["id"] = uuid.uuid4().hex[:8]
                elif channel == "feedback":
                    data["feedback"]["id"] = uuid.uuid4().hex
                else:
                    key = {"usage": "report_id", "surveys": "response_id", "activity": "batch_id"}[
                        channel
                    ]
                    data[key] = uuid.uuid4().hex
                sent = json.dumps(data, indent=2)
                sink = HttpExportSink(public_url + "/v1/" + channel)
                receipt = sink.send(sent)
                assert receipt.status == "stored"
                assert sink.send(sent).status == "duplicate"
                # Save synthetic examples for inspecting exact sent bytes during this run.
                (root / f"{channel}-sent.json").write_text(sent)
                print(f"HTTPS {channel}: stored; digest and duplicate receipt verified", flush=True)
            print(f"TEMPORARY_HTTPS_ENDPOINT={public_url}", flush=True)
            print(f"SYNTHETIC_EXAMPLES={root}", flush=True)
            print(
                "Do not use real research data. Production package destinations are unchanged.",
                flush=True,
            )
            if keep_alive_seconds:
                expires = datetime.now(UTC) + timedelta(seconds=keep_alive_seconds)
                print(
                    f"Expires at {expires.isoformat()} or when stopped. Test data is deleted on exit.",
                    flush=True,
                )
                deadline = time.monotonic() + keep_alive_seconds
                while time.monotonic() < deadline and tunnel.poll() is None:
                    time.sleep(min(5, max(0, deadline - time.monotonic())))
        finally:
            stop_process(tunnel)


def run(collector, *, public=False, keep_alive_seconds=0):
    wrangler = collector / "node_modules/.bin/wrangler"
    if not wrangler.exists() or not shutil.which("node"):
        raise RuntimeError(
            "Install Node.js and run npm ci in the companion benchside-ingest checkout first"
        )
    if not (collector / "src/metascience.ts").is_file():
        raise RuntimeError(
            "Use the collector review branch containing the survey and activity routes"
        )
    with tempfile.TemporaryDirectory(prefix="benchside-endpoint-test-") as temporary:
        root = Path(temporary)
        shutil.copytree(collector / "src", root / "src")
        (root / "node_modules").symlink_to(collector / "node_modules", target_is_directory=True)
        catalog = json.loads((ROOT / "tests/fixtures/metascience/catalog.json").read_text())
        today = datetime.now(UTC).date()
        catalog["studies"][0].update(
            opens=(today - timedelta(days=1)).isoformat(),
            closes=(today + timedelta(days=1)).isoformat(),
            title=f"Synthetic local check {root.name}",
        )
        catalog["studies"][0]["questions"].append(
            {"id": "comment", "type": "text", "prompt": "What was the synthetic problem?",
             "max_length": 2000}
        )
        (root / "src/studies.json").write_text(json.dumps(catalog))
        # Build a local-only config: never copy account IDs, routes or cloud environments.
        config = {
            "name": "benchside-local-check",
            "main": "src/index.ts",
            "compatibility_date": "2026-10-01",
            "workers_dev": False,
            "vars": {"ENVIRONMENT": "local-test"},
            "r2_buckets": [
                {"binding": c.upper(), "bucket_name": f"benchside-local-{c}"} for c in CHANNELS
            ],
            # The full synthetic check exceeds the production limit in one minute.
            # Production rate-limit behavior is separately covered by Worker tests.
            "ratelimits": [
                {
                    "name": "PER_SENDER",
                    "namespace_id": "4203",
                    "simple": {"limit": 100, "period": 60},
                }
            ],
        }
        config_path = root / "wrangler.json"
        config_path.write_text(json.dumps(config))
        port, inspector = available_port(), available_port()
        while inspector == port:
            inspector = available_port()
        endpoint = f"http://127.0.0.1:{port}"
        env = {
            **os.environ,
            "CLOUDFLARE_SEND_METRICS": "false",
            "WRANGLER_LOG_PATH": str(root / "wrangler.log"),
        }
        print(
            "Starting a temporary local collector; no Cloudflare login or deployment.", flush=True
        )
        with (root / "server.log").open("w+") as log:
            server = subprocess.Popen(
                [
                    str(wrangler),
                    "dev",
                    "--config",
                    str(config_path),
                    "--local",
                    "--ip",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--inspector-port",
                    str(inspector),
                    "--persist-to",
                    str(root / "storage"),
                    "--show-interactive-dev-session=false",
                ],
                cwd=root,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 30
                while True:
                    if server.poll() is not None or time.monotonic() >= deadline:
                        log.flush()
                        log.seek(0)
                        raise RuntimeError("Local Worker failed to start:\n" + log.read()[-6000:])
                    try:
                        with urlopen(f"{endpoint}/v1/studies", timeout=0.5) as response:
                            served = json.load(response)
                        if served != catalog:
                            raise RuntimeError("Unexpected local server; no submissions were made")
                        break
                    except (URLError, TimeoutError, OSError):
                        time.sleep(0.2)
                payloads = {}
                for channel, fixture in (
                    ("gaps", "benchside-export.json"),
                    ("feedback", "benchside-feedback.json"),
                    ("usage", "benchside-usage-demographics.json"),
                ):
                    payload = (collector / "test/fixtures" / fixture).read_text()
                    payloads[channel] = payload
                    sink = HttpExportSink(f"{endpoint}/v1/{channel}", allow_local=True)
                    assert sink.send(payload).status == "stored"
                    assert sink.send(payload).status == "duplicate"
                    print(f"{channel}: stored and exact-retry receipt verified", flush=True)
                payloads.update(smoke(endpoint))
                if public:
                    public_check(endpoint, root, env, payloads, catalog, keep_alive_seconds)
                print(
                    "PASS: all five submission routes. Temporary server and data will be removed."
                )
            finally:
                stop_process(server)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collector", type=Path, default=ROOT.parent / "benchside-ingest")
    parser.add_argument(
        "--public", action="store_true", help="open an isolated temporary HTTPS test receiver"
    )
    parser.add_argument(
        "--keep-alive-seconds",
        type=int,
        default=0,
        help="keep the public test receiver running after checks (maximum 3600)",
    )
    args = parser.parse_args()
    if not 0 <= args.keep_alive_seconds <= 3600 or (args.keep_alive_seconds and not args.public):
        parser.error("keep-alive must be 0–3600 seconds and requires --public")
    run(args.collector.resolve(), public=args.public, keep_alive_seconds=args.keep_alive_seconds)
