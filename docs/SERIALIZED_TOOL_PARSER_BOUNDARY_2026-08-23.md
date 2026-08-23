# Serialized Tool Parser Boundary — 2026-08-23

## Decision

The wire-format/parser gate **passes conditionally** in the synthetic typed-tool benchmark.

The retained decoder architecture is:

```text
bounded wire payload
  -> object/array-distinguishing JSON parse
  -> duplicate-field rejection
  -> exact schema/version/tool match
  -> exact security-number parsing
  -> explicit canonicalization rules only
  -> external authority binding
  -> one-shot token freshness / replay prevention
  -> canonical internal call
  -> downstream authorization / commit binding
```

The key negative result is that **schema validity alone is not enough**. A strict schema without token freshness still executed replayed authorizations in every retained run containing replay attacks.

## H — falsifiable hypotheses

1. Permissive/raw JSON handling can turn representation ambiguity into unsafe tool execution when gateway and executor semantics differ.
2. Strict schema validation removes parser ambiguity but does not provide authorization freshness.
3. One-shot token freshness closes replay that schema validation cannot.
4. Rejecting every noncanonical-but-unambiguous input is unnecessarily conservative; an explicitly specified canonicalization layer can recover utility without forwarding raw ambiguity.
5. The parser itself must reject malformed structures without uncaught exceptions or resource-unbounded parsing.

## T — experiment

Main retained run:

- 64 paired seeds;
- 420 proposals/seed;
- 32% adversarial/malformed wire payload rate;
- 4 policies: `lenient_raw`, `strict_schema`, `strict_fresh`, `canonical_fresh`.

Attack families:

- duplicate JSON field / parser differential;
- unknown field;
- missing required field;
- numeric string coercion;
- boolean-as-integer;
- NaN;
- Infinity;
- extreme negative/overflow-like magnitude;
- tiny underflow-scale decimal;
- negative zero;
- unit mismatch;
- zero-width tool spelling;
- Unicode confusable tool name;
- schema-version mismatch;
- actor-injected security field;
- replayed one-shot token;
- decimal precision smuggling above a hard limit;
- oversized payload.

Security numeric comparisons use `Decimal` before conversion to canonical internal numbers. The canonical contract allows at most six fractional decimal places. Strict parsing also applies a 16 KiB payload bound before JSON parsing.

## Main results

| policy | utility | unsafe leak rate | run violation rate | accept rate | malformed accepted |
|---|---:|---:|---:|---:|---:|
| lenient_raw | 0.70853 | 0.123996 | 1.000 | 0.94565 | 0.26191 |
| strict_schema | 0.72565 | 0.017783 | 1.000 | 0.70153 | 0.01778 |
| strict_fresh | 0.74699 | **0** | **0** | 0.68374 | 0 |
| canonical_fresh | **0.78690** | **0** | **0** | **0.73363** | 0.04989 |

The accepted malformed inputs under `canonical_fresh` are only explicitly supported normalization cases (for example plain decimal strings, `cents` converted once into canonical base units, and negative zero normalized to zero). The raw wire payload is not forwarded after normalization.

### Paired differences, 64 seeds

`canonical_fresh - strict_fresh`:

- utility: **+0.03991**, 95% CI **[+0.03799, +0.04183]**;
- unsafe-leak difference: exactly 0 in retained runs.

`canonical_fresh - lenient_raw`:

- utility: **+0.07838**, 95% CI **[+0.07145, +0.08531]**;
- unsafe leak: **-0.123996**, 95% CI **[-0.12830, -0.11969]**.

`strict_fresh - strict_schema`:

- utility: **+0.02134**, 95% CI **[+0.01950, +0.02318]**;
- unsafe leak: **-0.017783**, 95% CI **[-0.01932, -0.01625]**.

## Attack-level mechanism findings

### Duplicate fields

A permissive gateway using last-key-wins while a downstream executor uses first-key-wins allowed a safe-looking checked value to differ from the executed value. Strict duplicate rejection removed the ambiguity.

### NaN / non-finite values

A permissive negative-check pattern can allow NaN because ordinary comparisons are false. Strict finite-number validation rejects before authorization.

### Decimal precision smuggling

The payload `0.10000000000000001` can round to binary float `0.1`. A float-based gateway can therefore accept a value that is exactly above a `0.10` bound. Exact decimal comparison rejects it.

### Schema version and units

Treating an older wire schema or unit convention as if it were current can pass a value under one interpretation and execute a different magnitude under another. The retained path binds schema version and canonicalizes supported units exactly once.

### Actor security-field injection

Adding a schema-valid-looking `protected=false` claim cannot override the authoritative resource registry because actor-owned security fields are not part of the accepted proposal schema.

### Token replay

`strict_schema` rejected the parser attacks but accepted replayed otherwise-valid tokens. This alone caused nonzero leak and run-level violations. One-shot nonce freshness in `strict_fresh` and `canonical_fresh` removed the replay path.

## Parser implementation bug found by fuzzing

An early strict decoder used the same Python `list` representation for both JSON arrays and `object_pairs_hook` objects. Top-level arrays such as `[-1]` therefore reached object-unpacking code and caused uncaught `TypeError` / `ValueError` instead of clean rejection.

That implementation was invalidated.

The decoder now uses a dedicated `PairObject` marker type to distinguish JSON objects from arrays.

Final randomized structural fuzz:

- 100,000 malformed/random JSON values;
- **0 uncaught exceptions**.

This is a crash/robustness stress, not a proof of parser correctness.

## Clean control

At attack probability 0, all four policies achieved:

- utility = 1.0;
- accept rate = 1.0;
- unsafe leak = 0;
- benign false reject = 0.

Therefore the retained strict/canonical path did not penalize the benchmark's canonical clean traffic.

## D — decision

PASS, with explicit scope.

Retain:

1. parser objects and arrays must be structurally distinct;
2. duplicate and unknown fields are rejected unless explicitly namespaced/versioned;
3. security numbers are checked in exact decimal/fixed precision, not binary float;
4. schema and tool identifiers are exact, not fuzzy/confusable;
5. security attributes remain externally authoritative;
6. freshness/replay state is separate from schema validity;
7. if normalization is supported, it must be explicit and produce one canonical internal object; never validate one representation and execute the original raw payload;
8. payload size is bounded before parsing.

## C — failure modes / counter-hypotheses

The gate is not a proof for arbitrary production parsers. Remaining gaps include:

- actual JSON library/version differences across languages;
- cryptographic token implementation;
- expiration and distributed nonce-store consistency;
- remote tool protocols that may reparse or reinterpret canonical calls;
- Unicode normalization in external resource identifiers rather than tool names;
- parser CPU/memory denial beyond the tested 16 KiB boundary;
- real LLM proposal distributions.

## U — uncertainty

- Main results: 64 paired seeds × 420 proposals.
- Clean control: 64 paired seeds.
- Fuzz: 100,000 random malformed JSON values; zero uncaught exceptions after the object/array fix.
- Zero observed leak is conditional on this benchmark, implementation, attack suite, and stated TCB.

## Program action

Stop parser-threshold tuning. The next gate is a **frozen/live LLM proposer over mock tools** while preserving the exact same hard decoder / authority / commit boundary outside the model.
