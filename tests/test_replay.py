import json

from test_agents import gullible_model

from memgate_eval import CachedComplete, LLMAgent
from memgate_eval.replay import replay
from memgate_eval.sweeps import sweep


def make_run(folder, seeds=1, sessions=12, attacks=3):
    model = CachedComplete(gullible_model, log_path=folder / "transcript.jsonl", model="stand-in")
    agent = LLMAgent(model)
    summary = {
        "settings": {"seeds": str(seeds), "sessions": str(sessions), "ttl": "20",
                     "attacks": str(attacks), "fatigue": "0.1"},
        "under_attack": sweep(seeds, sessions, 20, 0.1, attacks, agent),
        "clean": sweep(seeds, sessions, 20, 0.1, 0, agent),
        "fatigue": [
            {"fatigue": f, **sweep(seeds, sessions, 20, f, attacks, agent, only="full")[0]}
            for f in (0.0, 0.1, 0.3, 0.5)
        ],
    }
    (folder / "summary.json").write_text(json.dumps(summary))
    return model.calls


def test_replay_reproduces_a_run_without_a_model_and_prunes_unused_replies(tmp_path):
    calls = make_run(tmp_path)
    with (tmp_path / "transcript.jsonl").open("a") as log:
        stale = {"step": "act", "model": "stand-in", "prompt": "left over", "reply": "{}"}
        log.write(json.dumps(stale) + "\n")

    result = replay(tmp_path, prune=True)
    assert result == {"matches": True, "rows": calls + 1, "used": calls}
    kept = (tmp_path / "transcript.jsonl").read_text().splitlines()
    assert len(kept) == calls and not any("left over" in line for line in kept)
    assert replay(tmp_path)["matches"]


def test_replay_reports_a_mismatch_and_leaves_the_transcript_alone(tmp_path):
    make_run(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text())
    summary["clean"][0]["ok_silent"]["mean"] += 0.01
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    before = (tmp_path / "transcript.jsonl").read_text()
    assert not replay(tmp_path, prune=True)["matches"]
    assert (tmp_path / "transcript.jsonl").read_text() == before
