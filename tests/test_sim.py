from memgate import presets
from memgate_eval import generate, run

P = presets(ttl=20)


def test_undefended_store_loses_to_every_attack():
    result = run(generate(1), P["none"])
    assert result["write_asr"] == 1.0
    assert result["asr"] == 1.0


def test_full_policy_blocks_everything_when_user_never_misclicks():
    result = run(generate(1), P["full"], fatigue=0.0)
    assert result["asr"] == 0.0
    assert result["residual_after_retraction"] == 0.0
    assert result["audit_ok"]


def test_full_policy_residual_risk_is_only_gap_filling():
    result = run(generate(2), P["full"], fatigue=1.0)
    assert result["asr_by_kind"]["extra_action"] == 0.0
    assert result["asr_by_kind"]["override"] == 0.0
    assert result["asr_by_kind"]["fill_gap"] > 0.0


def test_runs_are_deterministic():
    a = run(generate(3), P["full"], seed=3)
    b = run(generate(3), P["full"], seed=3)
    assert a == b


def test_clean_scenario_has_no_attacks():
    result = run(generate(4, n_attacks=0), P["full"])
    assert result["attacks"] == 0 and result["wrong"] == 0.0
