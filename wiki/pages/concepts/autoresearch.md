# AutoResearch — Karpathy LOOP FOREVER

**Tags**: autoresearch, karpathy, llm, f1-score, rule-improvement

## What It Is

AutoResearch is Karpathy's pattern for autonomous self-improvement of AI systems. Applied to FWA detection: the LLM proposes a new detection rule, validates it against a claims dataset, and commits or discards based on F1 improvement.

```
LOOP FOREVER:
  propose rule (LLM)
  evaluate F1 on sample claims
  if F1 improved → git commit (keep)
  else           → git reset --hard HEAD~1 (discard)
```

## Implementation in rxhcc-app

- 11 experiments hardcoded: `baseline + exp01–exp10`
- Best F1 achieved: **0.878**
- F1 progression: 0.821 → 0.829 → 0.837 → 0.843 → [discard] → 0.851 → 0.858 → 0.862 → [discard] → 0.878
- UI: progress bar, per-experiment table, inline SVG F1 line chart, LOOP FOREVER toggle

## React Implementation Pattern

Requires `useRef` + `useState` dual pattern to prevent stale closures in async loops.
See [[async-loop-stale-closure]] for the gotcha.

```js
const [arAutoLoop, setArAutoLoop] = useState(false);
const arAutoLoopRef = useRef(false);  // ref is read inside async callbacks

const runArExperiment = useCallback((idx) => {
  // ...
  arAutoLoopRef.current && runArExperiment(nextIdx);  // uses ref, not state
}, []);
```

## MCP Tool

`run_autoresearch` in `api/mcp.js`: accepts `currentF1`, `currentRules`, `sampleSize`. Returns `proposal` + `evaluation` (keep/discard decision).

**Related**: [[fwa-detection]], [[async-loop-stale-closure]], [[rxhcc-app]]
