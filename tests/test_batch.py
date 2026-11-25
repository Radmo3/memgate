import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from test_agents import gullible_model

from memgate_eval.batch import list_models, price_note, slug

ROOT = Path(__file__).resolve().parent.parent


def serve():
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._send(200, {"data": [
                {"id": "vendor-a/good-model", "pricing": {"prompt": "0.000001", "completion": "0.000005"}},
                {"id": "vendor-b/other-model"},
            ]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if body["model"] == "vendor-x/missing":
                self._send(404, {"error": {"message": "No such model"}})
                return
            system, user = (m["content"] for m in body["messages"])
            reply = "ok" if user == "ok?" else gullible_model(system, user)
            self._send(200, {"choices": [{"message": {"content": reply}}]})

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_slug_and_prices():
    assert slug("Vendor-A/Good Model:v2.1") == "vendor-a-good-model-v2.1"
    row = {"id": "x", "pricing": {"prompt": "0.000001", "completion": "0.000005"}}
    assert "$1.00 in / $5.00 out" in price_note(row)
    assert price_note({"id": "x"}) == ""


def test_list_models():
    server = serve()
    try:
        rows = list_models(f"http://127.0.0.1:{server.server_port}/v1", "k")
    finally:
        server.shutdown()
    assert [r["id"] for r in rows] == ["vendor-a/good-model", "vendor-b/other-model"]


def test_batch_runs_good_models_in_parallel_and_skips_a_bad_name(tmp_path):
    server = serve()
    env = dict(
        os.environ,
        PYTHONPATH=str(ROOT / "src"),
        MEMGATE_API_BASE=f"http://127.0.0.1:{server.server_port}/v1",
        MEMGATE_API_KEY="secret-key",
        no_proxy="127.0.0.1",
        NO_PROXY="127.0.0.1",
    )
    command = [
        sys.executable, "-m", "memgate_eval.batch",
        "--models", "vendor-a/good-model,vendor-x/missing,vendor-b/other-model",
        "--out-root", str(tmp_path), "--seeds", "1", "--sessions", "12", "--attacks", "3",
    ]
    try:
        done = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120)
    finally:
        server.shutdown()
    assert done.returncode == 1                       # one name was wrong
    assert "SKIPPED  vendor-x/missing" in done.stdout
    assert "secret-key" not in done.stdout + done.stderr
    for name in ("vendor-a-good-model", "vendor-b-other-model"):
        assert (tmp_path / name / "summary.md").exists()
        assert (tmp_path / name / "transcript.jsonl").exists()
    assert not (tmp_path / "vendor-x-missing").exists()
