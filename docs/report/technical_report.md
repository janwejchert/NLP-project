# ATC Readback Verifier: Technical Report

**NLP Group Project (Option 1: Application Development).** A proof-of-concept verification system, not production or operational software.
**Team (6):** Jan, Vlad, Felipe, Alberto, Kishan, Yi.
**Repository:** https://github.com/janwejchert/NLP-project - **Live demo:** https://nlp-project-atc.streamlit.app/ (Streamlit Community Cloud).

## Abstract

In air traffic control (ATC), a pilot reads a controller's instruction back so the controller can confirm it was heard correctly; an uncaught read-back error is a documented contributor to aviation incidents. We present the **ATC Readback Verifier**, a Streamlit web app that takes a controller instruction and a pilot read-back as text, extracts eight structured safety fields from each, and compares them with a deterministic Python comparator to return MATCH or a list of specific discrepancies. The architecture is deliberately hybrid: an LLM performs *only* extraction, while *all* correctness judgement is deterministic and auditable. On our own 50-case labelled test set, the final configuration (`qwen2.5:3b`) reaches F1 0.986 for error detection, a 6.2% false-alarm rate, and 100% detection recall in every error category. The most instructive result is a three-stage iteration showing that the comparator was never at fault, extraction is the bottleneck, and over-specific few-shot examples can *poison* a small model.

## 1. Introduction and justification of need

ATC communication relies on a closed loop: the controller issues a clearance, the pilot reads back the safety-relevant elements, and the controller listens to confirm correctness (the *hear-back*). This loop is the primary defence against miscommunication, yet it depends entirely on a human catching an error in real time, and an uncorrected error can remain undetected until a loss of separation appears on the controller's display. Foundational safety research quantifies the gap: FAA/Volpe analyses of NASA ASRS reports find that controllers catch only roughly two-thirds of incorrect read-backs, leaving about a third undetected, with error likelihood rising as a transmission carries more items.

Existing ATC speech and language tooling overwhelmingly targets a *different* task, **transcription**, turning radio audio into text, rather than **verification**, checking that a read-back faithfully matches the instruction. Commercial systems advertise transcription for cockpit displays but no clearance-verification function, and even the large public ATC corpora are built around collection, transcription, and concept extraction rather than a fielded verifier. Dedicated read-back-error-detection prototypes exist, almost entirely from European SESAR-funded research, but they remain at the lab stage with non-trivial false-alarm rates.

Our contribution is positioned squarely in that under-served niche: a lightweight, auditable, **text-based** field-by-field verifier with an explicit error taxonomy. We deliberately *verify correctness, not transcribe*. Audio / ASR is out of scope and treated as future work, which lets the project be a focused verification layer rather than another transcription front-end. As a course proof-of-concept we make no operational claims; the goal is a defensible, reproducible demonstration of the verification idea.

## 2. Field review (condensed synthesis)

Read-back/hear-back failure is a long-recognised aviation safety problem. SKYbrary and the ICAO information paper distinguish three failure modes: a read-back error the controller fails to catch, an absent read-back, and a "Type II" hear-back error where the controller misses a mistake in their *own* clearance even when the read-back was correct [1][2]. NASA ASRS work coined the "hear-back problem" and an associated study analysed several hundred reports [3][4]; the FAA/Volpe analysis by Cardosi and colleagues reports that controllers catch only ~two-thirds of incorrect read-backs and that error likelihood rises with message complexity, with headings, frequency changes, and altitudes among the most error-prone items [5][6]. Consistent contributing factors include confusable callsigns, expectation bias (e.g. hearing heading 280 as flight level 280), workload, and non-standard phraseology [1][3]. ICAO Annex 10, PANS-ATM (Doc 4444), and the Manual of Radiotelephony (Doc 9432) define the mandatory read-back items (callsign, runway, level/altitude, heading, speed, transponder code, QNH) which directly supplies a verifier's ground-truth field set [7][8], and EUROCONTROL's AGC action plan reinforces strict read-back discipline [9].

On the technology side, the ATCO2 corpus frames ATC understanding around three entity classes (callsign, command, value) and reports a fine-tuned-BERT NER baseline (F1 ~0.97 callsign, ~0.82 command, ~0.87 value), with command extraction hardest because utterances chain multiple commands and deviate from published phraseology [10][11]; ATCOSIM provides a cleaner benchmark [12], and self-supervised and Whisper-based ASR models have been fine-tuned and released for ATC [13][14], with surveillance-context fusion improving callsign recognition [15]. The clearest gap is that mature systems transcribe rather than verify [16][17], while the closest verification work, Helmke et al. in the HAAWAII project, performs concept-level comparison of controller-instruction against pilot read-back and reports ~80–81% detection on real recordings, finding semantic-concept comparison more robust than word-level matching [18][19]. Our design mirrors that concept-comparison insight while staying transparent: the LLM produces the ICAO mandatory items as structured fields and every judgement is deterministic Python. **The full review, with all references and verified source links, is in [`field_review.md`](field_review.md).**

## 3. System design

**Hybrid pipeline.** The system runs two extraction passes (one over the instruction, one over the read-back) that each turn free text into the same typed schema, then hands both to a deterministic comparator that emits a verdict:

```
  instruction text                read-back text
        │                               │
        ▼                               ▼
   Extractor (LLM)                 Extractor (LLM)      ← swappable backend
        │  ExtractedFields              │  ExtractedFields
        └───────────────┬───────────────┘
                        ▼
            Comparator (deterministic)   ★ the team's core IP
            field-by-field, normalized
                        ▼
            Verdict: MATCH | [Discrepancy, ...]
```

The LLM does *only* structured extraction: the well-bounded part a small free model handles well. All judgement (what counts as a match, normalization, which error category applies) is deterministic Python the team wrote, which maximises originality, reproducibility, and defensibility.

**Eight fields.** Extraction produces a typed schema of `callsign`, `altitude`, `heading`, `speed`, `frequency`, `squawk`, `runway`, and `qnh`, each `None` when absent. These map onto the ICAO mandatory read-back items.

**Normalization decisions.** Comparison is done on normalized values so that semantically equal read-backs match: spelled-out numbers become digits ("three thousand" → 3000), telephony is normalized ("one zero one three" → 1013), flight levels and feet are handled distinctly (FL280 vs 3000 ft), frequencies have trailing-zero normalization, squawk leading zeros are preserved, and runway captures designator plus optional side. For example, "climb three thousand feet, QNH 1013" is treated as equal to "climb altitude 3000 feet, QNH 1013".

**Deterministic comparator and the five-category error taxonomy.** The comparator compares each instruction field against its read-back counterpart and emits zero or more `Discrepancy` records. A read-back with no discrepancies is a MATCH. The five error categories are:

| Category | Meaning |
|---|---|
| `value_substitution` | a different value was read back (e.g. FL240 → FL250) |
| `digit_transposition` | the same digits in a different order: a more specific, higher-risk classification of a value error (e.g. runway 21 → 12) |
| `omission` | an instructed item was not read back |
| `callsign_error` | callsign wrong or missing |
| `added_element` | the read-back contains an item not instructed |

A key, defensible label-design choice is encoded here: which items are *mandatory* to read back versus informational. Wind, for instance, is informational, so a read-back that drops it is still a MATCH. The comparator is unit-tested (`tests/test_compare.py`) with no LLM or token required, and runs on every push via CI.

**Two free backends.** A single `Extractor` interface has two implementations selected by `EXTRACTOR_BACKEND`: **`ollama`** (local, default `qwen2.5:3b`) is used for development and the reproducible graded evaluation; **`hf`** (Hugging Face Inference API, `Qwen/Qwen2.5-7B-Instruct`) powers the hosted demo because the Streamlit Cloud free tier cannot run a local model. Both return the same typed fields, so the comparator and everything downstream are backend-agnostic and swapping is a one-line env change.

**The Streamlit app.** The user types the controller instruction and pilot read-back; the app runs the pipeline and returns MATCH, or DISCREPANCY with a human-readable list of specific problems and their categories. Input is text only.

## 4. Custom evaluation

**Test set.** We built our own labelled test set of **50 cases** (`eval/data/atc_readback_test_set.csv`, TC01–TC50), each an instruction/read-back pair with gold labels for `expected_verdict`, `error_category`, and `affected_field`. The set deliberately covers MATCH plus every error category, and includes hard cases by design (semantically-equal-but-differently-phrased read-backs, informational items like wind that must *not* trigger a discrepancy, and digit transpositions). Design and labelling are the team's own work.

**Metric framing.** The positive class is "the read-back contains an error" (a DISCREPANCY). Under that framing, precision/recall/F1 measure error **detection**. We additionally report the **false-alarm rate**, the fraction of genuinely correct read-backs that are wrongly flagged, which is the metric that matters most in a safety setting, since false alarms erode controller trust. We also report verdict accuracy (MATCH vs DISCREPANCY), per-category detection recall, and a confusion matrix.

**Headline result** (`ollama` / `qwen2.5:3b`, 50 cases, final configuration):

| Precision | Recall | F1 | False-alarm rate | Verdict accuracy |
|---|---|---|---|---|
| 0.971 | 1.000 | 0.986 | 6.2% | 0.980 |

**Confusion matrix (in prose).** Of the 50 cases, 16 are gold MATCH and 34 are gold DISCREPANCY. The system correctly identifies 15 of the 16 correct read-backs (true negatives) and flags 1 correct read-back in error (one false alarm: the 6.2% false-alarm rate). It detects all 34 erroneous read-backs (34 true positives, zero false negatives), which is why recall is a perfect 1.000. The single overall verdict failure is that one false alarm.

**Per-category detection recall.** Detection recall is **100% in every error category**: `value_substitution` (11/11), `omission` (8/8), `digit_transposition` (7/7), `callsign_error` (5/5), and `added_element` (3/3). Category accuracy is 1.000, every detected error (34/34) is given the correct category, and affected-field accuracy is 0.900. The full breakdown is in [`eval/results/metrics.md`](../../eval/results/metrics.md), regenerable with `make eval`.

## 5. Failure-mode analysis

We analysed failures across a **three-stage iteration** rather than as a single snapshot, because the iteration itself is the most informative result, it localises failure to the extraction step, not the comparator.

| Stage | Extractor | F1 | False-alarm | Verdict failures |
|---|---|---|---|---|
| Baseline | `qwen2.5:3b`, original prompt | 0.957 | 12.5% | 3 |
| Hardened (regression) | `3b`, +rules +examples | 0.944 | 25.0% | 4 |
| **Final** | `3b`, safe rules + comparator rule | **0.986** | **6.2%** | **1** |

**Stage 1: baseline.** Three distinct extraction weaknesses dominated: informational items leaking into clearance fields (the model mapped a *wind* "250 degrees / 8 knots" onto `heading=250` and `speed=8`), runway-side hallucination (inventing a "left" on one message and not the other), and inconsistent handling of multi-clause/gerund phrasing (missing a gerund-phrased "descending flight level 100").

**Stage 2: hardening regression and root cause.** We hypothesised that adding explicit rules and more few-shot examples would suppress the hallucinations. It **regressed**: recall hit 100% but the false-alarm rate *doubled* from 12.5% to 25% (four false alarms: TC08, TC11, TC12, TC13) and F1 fell. Inspecting the extracted fields revealed why. An added example pairing a squawk with the `Easy 4471` callsign taught the 3B model to read the **4-digit callsign suffix as a squawk code** (`Easy 4471` → `squawk 4471`); this created one new false alarm (TC12) and mis-categorised two genuine discrepancies (TC37, TC50, verdict still correct). Another example nudged it to misread `runway 24` as `heading 240` (TC13), and runway-side hallucination persisted (TC08, TC11). The lesson is concrete and defensible: **over-specific few-shot examples can poison a small model** in ways that generalise badly.

**Stage 3: the principled fix.** Two changes, neither a risky example: (1) a **deterministic comparator rule for runway side** (`_compare_runway`) that matches on the runway *number* and flags a side difference only when *both* messages explicitly state a side, model-independent and unit-tested; and (2) a clean prompt with **safe rules** (e.g. "squawk comes only from an explicit squawk instruction, never from the callsign's digits"). This resolved the wind leak (TC07), the runway-side false alarms (TC08, TC11), the squawk poisoning (fixing the TC37/TC50 mis-categorisations) and the heading hallucination (TC13), and caught the previously-missed added element (TC49), giving the best result on every metric. One false alarm remains (TC12), now for an unrelated reason discussed next.

**The one remaining failure (TC12).** On a two-clause instruction ("Easy 4471, reduce speed 210 knots, descend flight level 100." → "Speed 210 knots, descend flight level 100, Easy 4471."), the 3B model extracted `FL100` from the read-back but *dropped it from the instruction*, producing a spurious added-element discrepancy on a genuine MATCH. This is an extraction miss, not a comparator error, a capacity-bound limitation expected to resolve with a stronger extractor.

The same prompt and comparator were also run on `qwen2.5:7b` to test whether model capacity removes the residual extraction error. It does, decisively: 7B reaches **F1 1.000 with a 0% false-alarm rate and zero verdict failures**, correctly extracting the very two-clause instruction (TC12) the 3B model dropped. This confirms the residual failure is capacity-bound extraction, not a comparator flaw. The full 3B-vs-7B table and figures are in [`notebooks/analysis.ipynb`](../../notebooks/analysis.ipynb) (section 4). The overarching takeaways: the comparator is sound and extraction is the bottleneck; a reproducible harness turned "the prompt feels better" into a measured −18.8 pp false-alarm swing between attempts.

## 6. Limitations and future directions

This is a **text-only proof of concept**, not operational software; there is no auth, database, or live-radio audio path, and the hosted demo is best-effort while graded metrics come from the reproducible local run. Our own measurements show that **extraction is the bottleneck**: every observed failure traced to the LLM extraction step, never the deterministic logic. Small models also exhibit **variance and prompt sensitivity**: the same prompt can help or poison `qwen2.5:3b` depending on its examples, so results should be read as indicative of a 3B model under our prompt rather than a ceiling. The 50-case test set, while covering every category, is small, and a single false alarm or extraction miss moves the headline numbers noticeably. Future directions include an **ASR front end** (e.g. Whisper) to accept live radio audio, evaluation with **larger or fine-tuned extractor models** (the 3B-vs-7B comparison is a first step), a **larger and more diverse test set** with more accents and phraseology variants, phonetic/NATO-alphabet robustness, and confidence scoring with a controller-facing alerting UX.

## 7. Use of AI tools

Consistent with the assignment, we used an LLM assistant for brainstorming and scoping, boilerplate and scaffolding, first-draft prose, and AI-assisted literature search (every citation was checked against its primary source by a team member). All substantive intellectual decisions remained the team's own: the problem framing (verifying correctness, not transcribing), the test-set design and labels, the five-category error taxonomy, the comparison and normalization logic, the evaluation methodology including the false-alarm-rate and positive-class framing, and the interpretation of every result. Separately, the two Qwen2.5 extractor models are *part of the product*, not authoring aids, and perform field extraction only. The full account is in [`use_of_ai_tools.md`](use_of_ai_tools.md), and every member is prepared to defend the design, labels, methodology, and results independently in the Q&A.

## 8. Conclusion

The ATC Readback Verifier demonstrates that read-back *verification*, distinct from transcription, can be performed with a transparent hybrid design in which a small free LLM extracts structured fields and deterministic Python makes every judgement. On our own 50-case test set the final configuration detects every erroneous read-back (recall 1.000), reaches F1 0.986, and keeps the safety-critical false-alarm rate to 6.2%, with 100% detection recall in all five error categories. The most valuable lesson is grounded directly in our measurements: across the three-stage iteration the comparator was never the cause of a failure, a naive prompt-hardening attempt *regressed* by poisoning the small model's extraction, and a principled fix combining a deterministic comparator rule with safe prompt rules recovered and improved the result. Extraction, not comparison, is the bottleneck, and the residual failure is capacity-bound, which is exactly what a stronger extractor or an ASR-driven extension would target next. As a course proof of concept the system is intentionally scoped, but it is reproducible, auditable, and honest about what it does and does not yet do.

## References

Full reference list with verified source links is in [`field_review.md`](field_review.md). Citation numbers [1]–[19] in Section 2 above correspond one-to-one to that list.
