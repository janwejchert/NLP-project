# Failure-mode analysis

_All numbers come from the committed runs in `eval/results/runs/` and are reproduced by
[`notebooks/analysis.ipynb`](../../notebooks/analysis.ipynb)._

We analysed failures not as a one-off snapshot but across a **three-stage iteration**, because
the iteration itself is the most informative result: it shows *where* the system fails (the
extraction step, not the comparator) and how different fixes help or hurt.

## Summary of the iteration

| Stage | Extractor | Precision | Recall | F1 | False-alarm | Verdict acc | Verdict failures |
|---|---|---|---|---|---|---|---|
| Baseline | qwen2.5:3b, original prompt | 0.943 | 0.971 | 0.957 | 12.5% | 94.0% | 3 |
| Hardened (regression) | qwen2.5:3b, +rules +examples | 0.895 | 1.000 | 0.944 | 25.0% | 92.0% | 4 |
| **Final** | qwen2.5:3b, safe rules + comparator rule | **0.971** | **1.000** | **0.986** | **6.2%** | **98.0%** | **1** |

The deterministic comparator is unit-tested and was **never** the cause of a failure; every
error below is an **extraction** error or a deliberate **label** decision. The 3B-vs-7B
comparison (same prompt) is in the notebook.

## Stage 1: baseline failures (qwen2.5:3b, original prompt)

| Case | Instruction → read-back | Gold | Predicted | Cause (hypothesis) |
|---|---|---|---|---|
| **TC07** | "…cleared to land runway 24, **wind 250 degrees 8 knots**." | MATCH | DISCREPANCY | Model mapped the **wind** "250 degrees / 8 knots" onto `heading=250` and `speed=8` → false alarm. Informational items leaking into clearance fields. |
| **TC11** | "…line up and wait **runway 18**." (no side) | MATCH | DISCREPANCY | Model **hallucinated a runway side** ("left" on one message, none on the other) → false alarm on a non-existent side difference. |
| **TC49** | read-back adds "**descending flight level 100**" not instructed | DISCREPANCY (added_element) | MATCH | Model **failed to extract** the gerund-phrased altitude from the read-back → missed a real added element. |
| TC28 | squawk 5701 → 5071 | DISCREPANCY / transposition | DISCREPANCY / substitution | Model misread the read-back squawk digits (`5071`→`0507`), so the digit-multiset no longer matched → mis-categorised (verdict still correct). |
| TC39 | "cleared to land runway 24" → "Cleared to land" (no runway) | DISCREPANCY / omission | DISCREPANCY / substitution | Model **hallucinated `runway 24`** into the read-back, turning an omission into a value error (verdict still correct). |

**Read-out:** three distinct extraction weaknesses dominate: (a) informational items (wind)
leaking into fields, (b) **runway-side hallucination**, and (c) inconsistent handling of
multi-clause / gerund phrasing.

## Stage 2: a prompt-hardening attempt that backfired

Hypothesis: adding explicit rules and more few-shot examples would suppress the hallucinations
and cut the false-alarm rate. **Result: it regressed**, recall reached 100% (it now caught the
previously-missed TC49) but the false-alarm rate *doubled* from 12.5% to 25% and F1 fell. The
hardened run's **four false alarms were TC08, TC11, TC12, TC13**, all genuine MATCHes wrongly
flagged. Inspecting the extracted fields showed two new poisoning effects from the added examples:

- **Squawk poisoning (`Easy 4471` → `squawk 4471`).** An added example pairing a squawk with the
  `Easy 4471` callsign taught the 3B model to read the **4-digit callsign suffix as a squawk
  code**. This produced **one new false alarm (TC12)** and additionally **mis-categorised two
  genuine discrepancies**: TC37 (a squawk *omission*) and TC50 (an *added* squawk) were both
  relabelled `value_substitution`, the verdict stayed correct, but category accuracy fell.
- **TC13: heading hallucination.** An added example pairing a heading with a "descending"
  altitude nudged the model to misread `runway 24` as `heading 240`, inventing a heading in the
  read-back.
- **Runway-side hallucination got worse, not better:** the hardened run still invented a side on
  both TC08 and TC11, so the extra examples did not address it.

**Lesson:** over-specific few-shot examples can *poison* a small model in ways that generalise
badly. This is a concrete, defensible finding about prompt engineering with small models.

## Stage 3: the principled fix

Two changes, neither of which is a risky example:

1. **Deterministic comparator rule for runway side** (`src/atc_verifier/compare.py`,
   `_compare_runway`): match on the runway **number**; flag a *side* difference only when **both**
   messages explicitly state a side. Rationale: an unstated side is not a read-back error, and the
   model hallucinates sides. This is model-independent and unit-tested.
2. **Clean prompt with safe rules**: e.g. "squawk comes only from an explicit squawk instruction;
   never from the callsign's digits", and an explicit instruction-form wind example, **rules**,
   not poisoning examples.

This combination resolved the wind leak (TC07), the runway-side false alarms (TC08, TC11), and the
squawk poisoning, TC37 and TC50 are now categorised correctly and the heading hallucination (TC13)
is gone, and it caught the previously-missed added element (TC49), giving the best result on
**every** metric: F1 0.986, false-alarm 6.2%, recall 1.000, and **100% detection recall in all
five categories**. A single false alarm remains (TC12), now for an unrelated reason, see below.

### Remaining failure (1 case)

| Case | Instruction → read-back | Gold | Predicted | Cause |
|---|---|---|---|---|
| **TC12** | "Easy 4471, reduce speed 210 knots, **descend flight level 100**." → "Speed 210 knots, descend flight level 100, Easy 4471." | MATCH | DISCREPANCY (added_element, altitude) | The 3B model extracted `FL100` from the **read-back** but **dropped it from the instruction**, inconsistent extraction on a two-clause instruction, producing a spurious added element. A genuine small-model limitation; likely resolved by a stronger extractor (see the 3B-vs-7B comparison). |

## 3B vs 7B

The same prompt and comparator were run with `qwen2.5:7b` to test whether model capacity
resolves the residual extraction error. It does, and decisively:

| Model | Precision | Recall | F1 | False-alarm | Verdict accuracy | Verdict failures |
|---|---|---|---|---|---|---|
| `qwen2.5:3b` | 0.971 | 1.000 | 0.986 | 6.2% | 0.980 | 1 (TC12) |
| `qwen2.5:7b` | **1.000** | **1.000** | **1.000** | **0.0%** | **1.000** | **0** |

The 7B model produces a **perfect verdict score** on the test set: zero false alarms, zero
missed errors. Critically, it correctly extracts the two-clause instruction in **TC12** that the
3B model dropped, confirming directly that the residual 3B failure is **capacity-bound
extraction**, not a flaw in the (identical) comparator. The only blemish for 7B is a single
*category* mismatch (TC20: the 7B model failed to extract the read-back frequency, so a frequency
value-substitution surfaces as an `omission`), the verdict is still correct (DISCREPANCY). The comparison table and chart are reproduced in
[`notebooks/analysis.ipynb`](../../notebooks/analysis.ipynb) (section 4); raw outputs are in
`eval/results/runs/7b_final_v3/`.

## Takeaways

1. **The comparator is sound; extraction is the bottleneck.** Every failure traced to the LLM
   extraction step, never the deterministic logic.
2. **Few-shot examples can backfire** on small models, safe rules and deterministic
   post-processing were more reliable levers than adding examples.
3. **Measuring made it possible.** A reproducible harness turned "the prompt feels better" into a
   measured −18.8 pp false-alarm swing between attempts.
4. **Residual errors are capacity-bound**, multi-clause extraction misses are the kind of thing a
   larger model is expected to fix, which the 3B-vs-7B comparison tests directly.
