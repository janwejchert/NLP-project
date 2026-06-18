# Individual Reflection — Yi

**Role:** Report, field review, and project coordination — owner of `docs/report/` and the slide deck.

## My specific contributions

I wrote the technical report and authored `docs/report/field_review.md`, the literature review that positions our verifier at the intersection of aviation safety, ATC language understanding, and structured extraction. I built the justification-of-need narrative around primary sources I verified one-by-one: NASA ASRS's "hear-back problem" (Monan, and the 417-report / 29-month study), the FAA/Volpe finding (Cardosi) that controllers catch only ~two-thirds of incorrect read-backs, and ICAO Annex 10 / Doc 4444 / Doc 9432, which define the seven mandatory spoken read-back items (callsign, runway, level/altitude, heading, speed, transponder code, QNH); we added frequency as the eighth typed field, giving our 8-field schema. I anchored our design choice in the ATCO2 callsign/command/value framing and BERT NER baselines, and in HAAWAII's concept-level read-back-error detection (~80–81%), which mirrors our extract-then-compare approach. I articulated the gap — mature ATC speech systems transcribe rather than verify — and coordinated the team, keeping every reported claim tied to Alberto's eval output rather than to the literature.

## What I learned (NLP and engineering)

I learned that a field review is an argument, not a list: each citation had to earn its place by justifying a concrete design decision, e.g. ICAO mandatory items defining our field set, and HAAWAII's finding that semantic-concept comparison is more robust than word-level matching justifying why Vlad's deterministic comparator beats string-equality. On the NLP side, the ATCO2 baselines taught me why command extraction is the hard sub-task and why our 8 typed fields are a tractable scope. I also learned to separate fallible extraction from auditable judgement when explaining the system to non-specialists.

## Challenges and how I handled them

The hardest part was citation integrity. Several attractive figures (e.g. specific TRACON percentages) lived only in secondary summaries, so I flagged them in-text as "confirm against the primary PDF" rather than assert them. I also had to keep the report honest about our one residual failure, TC12 — an extraction miss, not a comparator error — and frame the iteration story (FA 12.5% to a regressed 25% to a principled 6.2%) as evidence that small models can be poisoned by over-specific few-shot examples, not as a comparator weakness.

## If I did it again

I would lock the field set against ICAO sources before any prompt work began, and I would version every claim in the report next to the exact eval run that produced it, so a reviewer in Q&A can trace 0.986 F1 straight to the harness output.

## Use of AI tools (personal note)

I used an AI assistant to draft prose and suggest related literature, but I treated every reference as unverified until I opened the original — checking the 417-report figure in the NASA TRS PDF and the two-thirds catch rate in the Cardosi study myself. Suggested sources I could not confirm against a primary document were cut, not softened.
