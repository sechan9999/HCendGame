# Lesson: Async Loop Stale Closure in React

**Tags**: react, useref, usestate, stale-closure, async, autoresearch

## Problem

AutoResearch LOOP FOREVER: toggling a boolean state `arAutoLoop` to stop the loop doesn't work inside an async callback — the callback captured the old value of `arAutoLoop` at the time it was created (stale closure).

```js
// BROKEN — stale closure
const [arAutoLoop, setArAutoLoop] = useState(false);
const run = async (idx) => {
  await doWork();
  if (arAutoLoop) run(idx + 1);  // always reads initial false — never loops
};
```

## Fix: useRef + useState Dual Pattern

Use `useState` for rendering (React needs to re-render on change), `useRef` for reading inside async callbacks (ref is always current):

```js
const [arAutoLoop, setArAutoLoop] = useState(false);
const arAutoLoopRef = useRef(false);

// When toggling, update BOTH:
const toggle = () => {
  const next = !arAutoLoop;
  setArAutoLoop(next);         // triggers re-render
  arAutoLoopRef.current = next; // ref is immediately current
};

// Inside async callback — read from ref, not state:
const run = useCallback(async (idx) => {
  await doWork();
  if (arAutoLoopRef.current) run(idx + 1);  // always current ✅
}, []);  // empty deps — stable reference
```

## Why useCallback with [] deps?

`useCallback` with empty deps creates a stable function reference. Without it, `run` would be recreated every render, causing the `useEffect` dependency chain to re-trigger incorrectly.

## Pattern Summary

| Need | Tool |
|------|------|
| Trigger re-render | useState |
| Read current value in async callback | useRef |
| Stable function reference | useCallback([]) |
| Chain reactions on state change | useEffect([state]) |

**Related**: [[autoresearch]]
