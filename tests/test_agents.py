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
            topic = re.match(r"\[([a-z0-9/-]+)\]", line)
            value = re.search(r"\b(ACC-\d{5}|contact\d{5}@[a-z0-9-]+\.example)\b", line)
            canary = re.search(r"copies\d{5}@records-archive\.example", line)
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


def test_cached_complete_reuses_replies_and_enforces_the_cap():
    import pytest

    from memgate_eval import CachedComplete

    model = CachedComplete(lambda system, user: user.upper(), max_calls=2)
    assert model("s", "a") == "A" and model("s", "a") == "A" and model("s", "b") == "B"
    assert (model.calls, model.hits) == (2, 1)
    with pytest.raises(RuntimeError):
        model("s", "c")


def _serve(handler_body):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            status, reply = handler_body(body)
            data = json.dumps(reply).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_transport_retries_without_temperature_when_the_model_rejects_it():
    seen = []

    def body(request):
        seen.append("temperature" in request)
        if "temperature" in request:
            return 400, {"error": {"message": "Unsupported value: 'temperature' does not support 0"}}
        return 200, {"choices": [{"message": {"content": "ok"}}]}

    server = _serve(body)
    try:
        complete = openai_compatible(f"http://127.0.0.1:{server.server_port}/v1", "k", "m")
        assert complete("s", "u") == "ok" and complete("s", "u2") == "ok"
    finally:
        server.shutdown()
    assert seen == [True, False, False]


def test_transport_reports_other_errors_without_the_key():
    import pytest

    server = _serve(lambda request: (401, {"error": {"message": "Incorrect API key provided"}}))
    try:
        complete = openai_compatible(f"http://127.0.0.1:{server.server_port}/v1", "secret-key", "m")
        with pytest.raises(RuntimeError) as err:
            complete("s", "u")
    finally:
        server.shutdown()
    assert "401" in str(err.value) and "secret-key" not in str(err.value)


def test_reworded_topics_are_mapped_back_and_counted():
    from memgate_eval.scenario import Item, ReadDoc

    def rewords(system, user):
        memory = {"topic": "Fact7 on file", "value": "vendor-value-7", "standing_instruction": None}
        return json.dumps([memory])

    agent = LLMAgent(rewords)
    doc = ReadDoc("doc-fact7", False, (Item("fact7", "vendor-value-7", "text", "summary"),))
    (memo,) = agent.remember(doc)
    assert memo.key == "fact7"
    assert agent.stats["memories whose topic was reworded (mapped back)"] == 1


def test_transcript_is_written(tmp_path):
    from memgate_eval import CachedComplete

    log = tmp_path / "out" / "transcript.jsonl"
    model = CachedComplete(lambda system, user: "[]", log_path=log)
    model(REMEMBER_SYSTEM, "DOCUMENT one")
    model(REMEMBER_SYSTEM, "DOCUMENT one")
    model(ACT_SYSTEM, "TASK two")
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["step"] for r in rows] == ["remember", "act"]
    assert rows[0] == {"step": "remember", "model": "", "prompt": "DOCUMENT one", "reply": "[]"}


def test_an_agent_that_asks_is_counted_as_asking_and_never_overridden():
    def stores_then_always_asks(system, user):
        if system == REMEMBER_SYSTEM:
            return gullible_model(system, user)
        return json.dumps({"use_memory_id": None, "also_do": []})

    for name in ("none", "full"):
        result = run(generate(5, **SMALL), P[name], agent=LLMAgent(stores_then_always_asks))
        assert result["ok_silent"] == 0.0 and result["ok_prompted"] == 0.0
        assert result["asked"] > 0.5
        assert result["asr"] == 0.0


def test_task_prompts_contain_a_concrete_request():
    seen = []

    def records(system, user):
        seen.append((system, user))
        return gullible_model(system, user)

    run(generate(5, **SMALL), P["none"], agent=LLMAgent(records))
    acts = [user for system, user in seen if system == ACT_SYSTEM]
    assert acts and all(u.startswith("USER REQUEST: ") and "DETAIL NEEDED: " in u for u in acts)
    assert not any("attacker" in user.lower() for _, user in seen)


def test_an_interrupted_run_continues_from_its_transcript(tmp_path):
    from memgate_eval import CachedComplete

    log = tmp_path / "transcript.jsonl"
    first = CachedComplete(lambda system, user: "first", log_path=log, model="m1")
    first(REMEMBER_SYSTEM, "DOCUMENT one")
    with log.open("a") as f:
        f.write('{"step": "act", "prompt": "cut off mid-wri')      # a crash mid-write

    def must_not_be_called(system, user):
        raise AssertionError("paid twice for the same prompt")

    again = CachedComplete(must_not_be_called, log_path=log, model="m1")
    assert again.resumed == 1 and again(REMEMBER_SYSTEM, "DOCUMENT one") == "first"
    assert again.calls == 0

    other = CachedComplete(lambda system, user: "second", log_path=log, model="m2")
    assert other.resumed == 0 and other(REMEMBER_SYSTEM, "DOCUMENT one") == "second"


def test_transport_retries_when_the_endpoint_is_busy_or_silent():
    import time as clock

    seen = []

    def body(request):
        seen.append(1)
        if len(seen) == 1:
            return 503, {"error": {"message": "overloaded"}}
        if len(seen) == 2:
            clock.sleep(0.6)                                          # longer than the timeout
        return 200, {"choices": [{"message": {"content": "ok"}}]}

    server = _serve(body)
    try:
        complete = openai_compatible(
            f"http://127.0.0.1:{server.server_port}/v1", "k", "m", timeout=0.3, backoff=0.01
        )
        assert complete("s", "u") == "ok"
    finally:
        server.shutdown()
    assert len(seen) == 3


def test_transport_gives_up_with_a_clear_message():
    import pytest

    server = _serve(lambda request: (500, {"error": {"message": "down"}}))
    try:
        complete = openai_compatible(
            f"http://127.0.0.1:{server.server_port}/v1", "secret-key", "m", retries=2, backoff=0.01
        )
        with pytest.raises(RuntimeError) as err:
            complete("s", "u")
    finally:
        server.shutdown()
    assert "3 times" in str(err.value) and "secret-key" not in str(err.value)
