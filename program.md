# RxHCC FWA AutoResearch

This is the agentic research program for the **RxHCC Fraud, Waste & Abuse (FWA) Detection System**, modeled after the [autoresearch](https://github.com/sechan9999/autoresearch) philosophy.

The idea: give an AI agent the fraud detection system and let it autonomously experiment with new detection rules, measure precision/recall, and iteratively improve the rule engine — just like how autoresearch improves an LLM training loop.

---

## Setup

To set up a new experiment run:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar7`).
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**:
   - `README.md` — repository context
   - `engine/rules.py` — the PRIMARY file you modify. Contains all fraud detection rules, ICD/NDC mappings, HCC validation logic.
   - `engine/sagemaker_replication.py` — synthetic data generator. Do NOT modify.
   - `engine/langgraph_integrity.py` — validation orchestration. Read-only.
4. **Read the current baseline metrics** from `results.tsv` (if it exists, else initialize it).
5. **Initialize results.tsv**: Create with header row and baseline entry.
   - Baseline: precision=0.82, recall=0.71, f1=0.76 (estimated from 500-claim batch demo)
6. **Confirm and go.**

---

## The Experiment Loop

The metric is **F1 Score** on the synthetic validation set (precision × recall balance).
Lower false positives → higher precision. Lower false negatives → higher recall.

LOOP FOREVER:

1. Review current `engine/rules.py` — understand all active rules.
2. Propose and implement one experiment idea in `engine/rules.py`.
3. `git commit`
4. Run validation: 
   ```
   python -c "
   from engine.sagemaker_replication import SyntheticClaimGenerator, PandasBatchValidator
   gen = SyntheticClaimGenerator(seed=42)
   df = gen.generate(500, 0.15)
   v = PandasBatchValidator()
   out = v.validate_dataframe(df)
   s = v.get_summary(out)
   tp = sum(1 for _, r in out.iterrows() if r.anomaly_type != 'normal' and r.is_flagged)
   fp = sum(1 for _, r in out.iterrows() if r.anomaly_type == 'normal' and r.is_flagged)
   fn = sum(1 for _, r in out.iterrows() if r.anomaly_type != 'normal' and not r.is_flagged)
   prec = tp/(tp+fp) if tp+fp > 0 else 0
   rec = tp/(tp+fn) if tp+fn > 0 else 0
   f1 = 2*prec*rec/(prec+rec) if prec+rec > 0 else 0
   print(f'precision={prec:.4f} recall={rec:.4f} f1={f1:.4f}')
   " > run.log 2>&1
   ```
5. Read results: `grep "f1=" run.log`
6. If crash, check `tail -20 run.log`.
7. Record in `results.tsv`.
8. **If F1 improved (higher)**: advance branch (keep commit).
9. **If F1 equal or worse**: `git reset --hard HEAD~1` (revert).

---

## What You CAN Do (in `engine/rules.py`)

- Add new ICD-NDC mapping rules
- Add or tighten HCC upcoding detection thresholds
- Add new drug conflict rules (e.g., incompatible cocktails)
- Add provider-level anomaly scoring
- Tune risk score thresholds
- Add new anomaly types (e.g., place-of-service mismatches, temporal billing patterns)
- Add compound rules (A AND B → flag)

## What You CANNOT Do

- Modify `engine/sagemaker_replication.py` — it is the ground truth data generator
- Modify `engine/langgraph_integrity.py` — it is the evaluation orchestrator  
- Add new Python package dependencies
- Modify the evaluation harness

---

## Simplicity Criterion

Same as autoresearch: simpler is better. A small F1 improvement that adds 50 lines of hacky code is not worth it. A simplification that maintains F1 is always a win. Keep the rule engine readable.

---

## Output Format

```
precision=0.8412
recall=0.7284
f1=0.7808
```

---

## Logging Results

File: `results.tsv` (tab-separated)

```
commit	f1	precision	recall	status	description
baseline	0.7600	0.8200	0.7100	keep	baseline (estimated)
a1b2c3d	0.7808	0.8412	0.7284	keep	tighten GLP-1 off-label threshold
b2c3d4e	0.7650	0.7900	0.7410	discard	too many FP on HCC rules
```

---

## Experiment Ideas to Try

Inspired by real-world FWA patterns:

1. **Temporal clustering**: flag providers who bill same patient >3x in 30 days
2. **HCC hierarchy violations**: lower-severity HCC billed when evidence supports only baseline
3. **Drug interaction fraud**: two competing drugs billed simultaneously (e.g., two GLP-1s)
4. **Place-of-service mismatch**: hospital-only drug billed in office setting
5. **Cascade billing**: NDC billed without associated E&M code (office visit)
6. **MA risk score inflation**: HCC codes appearing suddenly in December (annual risk adjustment gaming)
7. **Quantity limit violations**: NDC quantity exceeds days-supply for the diagnosis
8. **Specialty mismatch**: oncology drugs prescribed by non-oncologist without referral chain
9. **Lookback conflicts**: new chronic condition diagnosis without prior acute/lab evidence
10. **NDC unbundling**: separately billing components of a known compound drug

---

## About

This `program.md` is the AI researcher's instruction set for autonomous FWA rule improvement.
You are programming the **program**, not just the code.
The agent modifies `engine/rules.py`, measures F1, keeps or reverts — indefinitely until stopped.

*"One day, insurance fraud used to be caught by meat computers reviewing stacks of claims between coffee breaks and department meetings. That era is long gone."*
