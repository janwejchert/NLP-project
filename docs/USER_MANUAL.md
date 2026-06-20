# ATC Readback Verifier: User Manual

> Course project (NLP Group Project, Option 1). This is a proof of concept, **not certified for operational use**.

## Who it is for

This tool is for anyone who wants to check whether a pilot's **readback** correctly repeats a controller's **instruction**. In real air traffic control, an incorrect or incomplete readback, a wrong altitude, transposed digits, or an omitted item, is a documented contributor to aviation incidents (e.g. NASA's Aviation Safety Reporting System). The app extracts structured fields from each message, compares them field by field, and tells you whether the readback is a **MATCH** or contains a **DISCREPANCY**, with a specific list of problems.

## Starting the app

Setup (creating the virtual environment, installing dependencies, and choosing an extraction backend) is covered in [INSTALL.md](INSTALL.md). Once setup is complete, launch the app from the repository root with:

```bash
make run
```

This is equivalent to the manual command:

```bash
streamlit run app/streamlit_app.py
```

Streamlit will open the app in your browser (typically at `http://localhost:8501`). A hosted demo may also be available; see the project README.

## Walkthrough of the interface

The page has a main area with two text boxes and a **sidebar** with settings.

- **Controller instruction** (top text box): type or paste the controller's instruction, e.g. `Speedbird 245, climb flight level 280.`
- **Pilot readback** (second text box): type or paste the pilot's readback, e.g. `Climb flight level 280, Speedbird 245.`
- **Sidebar → Settings:**
  - **Extraction backend**: selects which model extracts the fields: `ollama` (a local model) or `hf` (the Hugging Face Inference API). The default follows your configuration.
  - **Model (optional override)**: leave blank to use the default model, or type a model name to override it (e.g. `qwen2.5:3b` or `Qwen/Qwen2.5-7B-Instruct`).
  - **Load an example**: pick one of the built-in example pairs to auto-fill both text boxes so you can try the app immediately.
- **Verify readback** (primary button): runs the verification. If either box is empty you will be prompted to fill both in. While it works, a short "Extracting fields and comparing…" spinner is shown.

## How to read the result

After you click **Verify readback**, one of two banners appears:

- **Green banner: `✅ MATCH: the readback is correct.`** The readback contains every instructed item, with no errors.
- **Red banner: `❌ DISCREPANCY: N issue(s) found.`** One or more problems were detected. Each problem is listed on its own line in the form:

  > **field** · _category_ - detail

  For example: **altitude** · _value substitution_ - instructed altitude FL240, read back as FL250.
  The **field** is which item was affected, the **category** is the kind of error (see below), and the **detail** is a plain-language explanation.

Below the banner is a **Show extracted fields** expander. Open it to see, side by side, the raw fields the model pulled from the instruction and from the readback. This is useful for understanding *why* a verdict was reached and for spotting cases where the extraction model misread the text.

## Reference: the 8 fields

| Field | Meaning | Example phrase |
| --- | --- | --- |
| **callsign** | Aircraft identity | "Speedbird 245" |
| **altitude** | Flight level or altitude in feet | "flight level 280", "3000 feet" |
| **heading** | Heading in degrees (with optional turn direction) | "turn left heading 270" |
| **speed** | Airspeed | "speed 250 knots" |
| **frequency** | Radio frequency | "contact Tower 118.7" |
| **squawk** | Transponder code (4 digits) | "squawk 5701" |
| **runway** | Runway designator | "runway 21 left" |
| **qnh** | Altimeter pressure setting | "QNH 1013" |

## Reference: the 5 error categories

- **value_substitution**: a different value was read back. *Example:* instructed FL240, read back FL250.
- **digit_transposition**: the same digits in a different order (a higher-risk failure mode). *Example:* runway 21 read back as 12.
- **omission**: an instructed item was not read back at all. *Example:* a frequency change was instructed but not repeated.
- **callsign_error**: the callsign is wrong or missing. *Example:* Speedbird 245 read back as Speedbird 254.
- **added_element**: the readback contains an item that was never instructed. *Example:* a squawk code appears in the readback but not the instruction.

A correct readback produces zero discrepancies, which is reported as **MATCH**.

## Examples to try

Use the sidebar **Load an example** picker, or type these in directly:

- **Correct readback (MATCH)**
  - Instruction: `Speedbird 245, descend flight level 240, turn left heading 270.`
  - Readback: `Descend flight level 240, left heading 270, Speedbird 245.`
- **Wrong altitude (value_substitution)**
  - Instruction: `Speedbird 245, descend flight level 240.`
  - Readback: `Descend flight level 250, Speedbird 245.`
- **Transposed runway (digit_transposition, 21 → 12)**
  - Instruction: `Vueling 38 Lima, line up and wait runway 21.`
  - Readback: `Line up and wait runway 12, Vueling 38 Lima.`
- **Omitted item (omission)**
  - Instruction: `Iberia 6020, turn right heading 120, contact Tower 118.7.`
  - Readback: `Right heading 120, Iberia 6020.`
- **Callsign error (callsign_error)**
  - Instruction: `Speedbird 245, climb flight level 280.`
  - Readback: `Climb flight level 280, Speedbird 254.`

## Limitations

- **Text only.** You type the instruction and readback as text. Live audio or speech-to-text is a possible future direction but is **not** built.
- **Depends on the extraction model.** Field extraction is done by an LLM; if it misreads a message, the comparison can be affected. The **Show extracted fields** expander helps you spot this. (The comparison logic itself is deterministic.)
- **Proof of concept.** This is a university course project. It is **not certified** and must not be used for real operational air traffic control.
