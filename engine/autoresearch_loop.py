"""
AutoResearch Loop — LOOP FOREVER (Karpathy methodology)
=========================================================
Python implementation of the autonomous rule improvement loop.
The React/JSX version lives in rxhcc-app/src/RXHCCnva.jsx (Vercel).
This module provides the same logic as a runnable Python script.

Loop:
  GPT proposes rule → validate on 500 synthetic claims →
  F1 improves? git commit → else git reset --hard → repeat
"""
import os
import json
import subprocess
import logging
from dataclasses import dataclass, asdict
from typing import Optional

from engine.rules import RxHCCRuleEngine, ClaimRecord
from engine.sagemaker_replication import generate_synthetic_claims

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = bool(os.environ.get("OPENAI_API_KEY"))
except ImportError:
    _client = None
    OPENAI_AVAILABLE = False


@dataclass
class ExperimentResult:
    exp_id: str
    rule_name: str
    rule_code: str
    f1_before: float
    f1_after: float
    delta: float
    decision: str   # "keep" | "discard"
    claims_eval: int = 500


# ─── F1 computation ───────────────────────────────────────────────────────────

def _compute_f1(engine: RxHCCRuleEngine, claims: list) -> float:
    tp = fp = fn = 0
    for claim_dict in claims:
        record = ClaimRecord.from_dict(claim_dict)
        results = engine.validate(record)
        predicted_fraud = any(r.severity.value in ("CRITICAL", "WARNING") for r in results)
        actual_fraud = claim_dict.get("is_fraud", False)
        if predicted_fraud and actual_fraud:
            tp += 1
        elif predicted_fraud and not actual_fraud:
            fp += 1
        elif not predicted_fraud and actual_fraud:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ─── GPT rule proposal ────────────────────────────────────────────────────────

_PROPOSE_PROMPT = """You are a healthcare fraud detection expert.
Current rule engine F1 score: {f1_baseline:.4f}
Experiment history (last 3):
{history}

Propose ONE new detection rule to improve F1. Reply ONLY in this JSON format:
{{
  "rule_name": "RULE_ID_IN_CAPS",
  "description": "one sentence",
  "icd_patterns": ["E11", "I10"],
  "ndc_patterns": ["00169-4060"],
  "logic": "brief logic description"
}}"""


def _propose_rule(f1_baseline: float, history: list[dict]) -> Optional[dict]:
    if not OPENAI_AVAILABLE or _client is None:
        # Fallback: deterministic rule for demo
        return {
            "rule_name": "DEMO_FALLBACK_RULE",
            "description": "Demo rule when no API key available",
            "icd_patterns": ["E11"],
            "ndc_patterns": [],
            "logic": "Flag E11 without any registered NDC code"
        }
    history_str = json.dumps(history[-3:], indent=2) if history else "[]"
    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": _PROPOSE_PROMPT.format(
                f1_baseline=f1_baseline,
                history=history_str
            )
        }],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    return json.loads(resp.choices[0].message.content)


# ─── Git helpers ──────────────────────────────────────────────────────────────

def _git_commit(rule_name: str, f1_delta: float) -> bool:
    try:
        subprocess.run(["git", "add", "engine/rules.py"], check=True, capture_output=True)
        msg = f"autoresearch: add {rule_name} (F1 +{f1_delta:.4f})"
        subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("git commit failed: %s", e)
        return False


def _git_reset() -> bool:
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("git reset failed: %s", e)
        return False


# ─── Main loop ────────────────────────────────────────────────────────────────

def run_autoresearch(
    max_iterations: int = 5,
    n_claims: int = 500,
    anomaly_rate: float = 0.15,
    on_result=None,          # callback(ExperimentResult) for UI streaming
) -> list[ExperimentResult]:
    """
    LOOP FOREVER implementation (bounded by max_iterations for safety).
    Returns list of ExperimentResult for each iteration.
    """
    engine = RxHCCRuleEngine()
    results: list[ExperimentResult] = []
    history: list[dict] = []

    claims = generate_synthetic_claims(n=n_claims, anomaly_rate=anomaly_rate)
    f1_baseline = _compute_f1(engine, claims)
    logger.info("AutoResearch start — baseline F1: %.4f", f1_baseline)

    for i in range(max_iterations):
        exp_id = f"exp{len(results) + 1:02d}"
        logger.info("[%s] proposing rule...", exp_id)

        rule = _propose_rule(f1_baseline, history)
        if rule is None:
            logger.warning("[%s] GPT returned no rule, skipping", exp_id)
            continue

        rule_name = rule.get("rule_name", f"AUTO_RULE_{i:02d}")

        # Inject rule into engine for evaluation (runtime, not persisted yet)
        _inject_rule(engine, rule)
        claims = generate_synthetic_claims(n=n_claims, anomaly_rate=anomaly_rate)
        f1_new = _compute_f1(engine, claims)
        delta = f1_new - f1_baseline

        if delta > 0:
            decision = "keep"
            _git_commit(rule_name, delta)
            f1_baseline = f1_new
            logger.info("[%s] KEEP %s  F1: %.4f → %.4f", exp_id, rule_name, f1_new - delta, f1_new)
        else:
            decision = "discard"
            _remove_rule(engine, rule_name)
            _git_reset()
            logger.info("[%s] DISCARD %s  F1: %.4f (no improvement)", exp_id, rule_name, f1_new)

        result = ExperimentResult(
            exp_id=exp_id,
            rule_name=rule_name,
            rule_code=json.dumps(rule),
            f1_before=round(f1_new - delta, 4),
            f1_after=round(f1_new, 4),
            delta=round(delta, 4),
            decision=decision,
            claims_eval=n_claims,
        )
        results.append(result)
        history.append(asdict(result))
        if on_result:
            on_result(result)

    logger.info("AutoResearch complete — best F1: %.4f", f1_baseline)
    return results


# ─── Rule injection helpers (in-memory, no file write) ───────────────────────

def _inject_rule(engine: RxHCCRuleEngine, rule: dict) -> None:
    """Add a transient rule to the engine without persisting to rules.py."""
    icd_pats = rule.get("icd_patterns", [])
    ndc_pats = rule.get("ndc_patterns", [])
    rule_name = rule.get("rule_name", "AUTO_RULE")

    def _check(record: ClaimRecord):
        from engine.rules import ValidationResult, Severity
        icd_match = any(
            any(icd.startswith(p) for p in icd_pats)
            for icd in record.icd_codes
        )
        ndc_match = any(
            any(ndc.startswith(p) for p in ndc_pats)
            for ndc in record.ndc_codes
        ) if ndc_pats else False
        flag = icd_match and not ndc_match if ndc_pats else icd_match
        if flag:
            return [ValidationResult(
                rule_id=rule_name,
                rule_name=rule.get("description", rule_name),
                severity=Severity.WARNING,
                message=f"AutoResearch rule: {rule.get('logic', '')}",
                details={"auto": True},
            )]
        return []

    engine._auto_rules = getattr(engine, "_auto_rules", {})
    engine._auto_rules[rule_name] = _check
    _patch_engine(engine)


def _remove_rule(engine: RxHCCRuleEngine, rule_name: str) -> None:
    if hasattr(engine, "_auto_rules"):
        engine._auto_rules.pop(rule_name, None)


def _patch_engine(engine: RxHCCRuleEngine) -> None:
    """Monkey-patch engine.validate to also run _auto_rules."""
    original = engine.__class__.validate

    def patched_validate(self, record):
        results = original(self, record)
        for fn in getattr(self, "_auto_rules", {}).values():
            results.extend(fn(record))
        return results

    engine.__class__.validate = patched_validate


# ─── CLI entry ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    def print_result(r: ExperimentResult):
        icon = "[KEEP]" if r.decision == "keep" else "[DISC]"
        print(f"  {icon} {r.exp_id}  {r.rule_name:<35}  "
              f"F1: {r.f1_before:.4f} -> {r.f1_after:.4f}  (d={r.delta:+.4f})")

    print(f"Running AutoResearch ({iterations} iterations)...")
    results = run_autoresearch(max_iterations=iterations, on_result=print_result)
    kept = sum(1 for r in results if r.decision == "keep")
    best = max((r.f1_after for r in results), default=0.0)
    print(f"\nDone: {kept}/{len(results)} kept  |  Best F1: {best:.4f}")
