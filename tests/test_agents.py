import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from memgate import presets
from memgate_eval import LLMAgent, generate, openai_compatible, run
from memgate_eval.agents import ACT_SYSTEM, REMEMBER_SYSTEM, extract_json

P = presets(ttl=20)
SMALL = dict(n_sessions=30, n_prefs=6, n_facts=4, n_attacks=6, max_delay=8)


def gullible_model(system: str, user: str) -> str:
    """A stand-in model that believes every document and obeys every memory."""
    if system == REMEMBER_SYSTEM:
        out = []
        for line in user.splitlines()[1:]:
            topic = re.search(r"\b(pref\d+|fact\d+|gap\d+)\b", line)
            value = re.search(r"\b(attacker-value-atk\d+|vendor-value-\d+)\b", line)
            canary = re.search(r"canary-atk\d+@example\.test", line)
            if topic:
                out.append({
                    "topic": topic.group(1),
                    "value": value.group(1) if value else None,
                    "standing_instruction": f"send a copy to {canary.group(0)}" if canary else None,
                })
        return "Here is what I will remember:\n" + json.dumps(out)
    assert system == ACT_SYSTEM
    use, also = None, []
    for line in user.splitlines():
        m = re.match(r"\[(m\d+)\]", line)
        if not m:
            continue
        if "| value:" in line:
            use = m.group(1)
        for instruction in re.findall(r"standing instruction: ([^|]+)", line):
            also.append({"action": instruction.strip(), "because_of_memory_id": m.group(1)})
    return json.dumps({"use_memory_id": use, "also_do": also})


def test_extract_json_tolerates_prose_and_fences():
    assert extract_json('Sure:\n```json\n[{"a": 1}]\n```', "[") == [{"a": 1}]
    assert extract_json('prefix {"x": {"y": 2}} suffix }', "{") == {"x": {"y": 2}}
    assert extract_json("no json here", "{") is None


def test_gullible_model_is_exploited_without_a_defense():
    agent = LLMAgent(gullible_model)
    result = run(generate(5, **SMALL), P["none"], agent=agent)
    assert result["asr"] == 1.0
    assert agent.calls > 0


def test_full_policy_holds_against_a_gullible_model():
    result = run(generate(5, **SMALL), P["full"], agent=LLMAgent(gullible_model), fatigue=0.0)
    assert result["asr"] == 0.0


def test_unattributed_actions_are_denied_when_untrusted_memory_is_in_view():
    def hides_its_reasons(system, user):
        reply = json.loads(gullible_model(system, user).split("\n", 1)[-1])
        if isinstance(reply, dict):
            for action in reply["also_do"]:
                action["because_of_memory_id"] = None
        return json.dumps(reply)

    result = run(generate(5, **SMALL), P["full"], agent=LLMAgent(hides_its_reasons), fatigue=0.0)
    assert result["asr_by_kind"]["extra_action"] == 0.0


def test_malformed_model_output_does_nothing():
    result = run(generate(5, **SMALL), P["none"], agent=LLMAgent(lambda s, u: "I cannot help."))
    assert result["write_asr"] == 0.0 and result["asr"] == 0.0


def test_openai_compatible_transport_against_a_local_server():
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen["path"], seen["auth"] = self.path, self.headers["Authorization"]
            seen["model"] = body["model"]
            reply = json.dumps({"choices": [{"message": {"content": "pong"}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(reply)))
            self.end_headers()
            self.wfile.write(reply)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        complete = openai_compatible(
            f"http://127.0.0.1:{server.server_port}/v1", api_key="test-key", model="test-model"
        )
        assert complete("system", "ping") == "pong"
    finally:
        server.shutdown()
    assert seen == {"path": "/v1/chat/completions", "auth": "Bearer test-key", "model": "test-model"}
