# Install & Execution Guide

This guide covers installing, configuring, running, evaluating, and deploying the
**ATC Readback Verifier** — a Streamlit proof-of-concept (POC) that checks whether a
pilot's readback matches a controller's instruction. It is a university NLP group
project, not production software.

All commands are run from the **repository root**.

## Prerequisites

- **Python 3.10+** (the team develops on 3.13).
- **git**.
- **Make** (standard on macOS/Linux; the `make` targets below are optional shortcuts).
- For the **local backend** (`ollama`): the **Ollama** app installed from
  <https://ollama.com> and **running** in the background.
- For the **Hugging Face backend** (`hf`, used by the hosted cloud demo): a free
  Hugging Face access token with **Read** scope, created at
  <https://huggingface.co/settings/tokens>.

You only need Ollama *or* a Hugging Face token, depending on which backend you choose.
The default (and the backend used for the reproducible evaluation) is `ollama`.

## 1. Clone the repository

```bash
git clone https://github.com/janwejchert/NLP.git
cd NLP
```

The full project — code, evaluation, and the report — is on the default `main`
branch, so the clone above is all you need.

## 2. Install

### Path A — `make setup` (recommended)

```bash
make setup
```

This creates a `.venv`, upgrades pip, installs `requirements.txt` +
`requirements-dev.txt`, and installs the package in editable mode (`pip install -e .`).
When it finishes, activate the environment:

```bash
source .venv/bin/activate
```

### Path B — manual (equivalent)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt && pip install -e .
```

## 3. Pull the local model (for the `ollama` backend)

Make sure the Ollama app is running, then:

```bash
make pull-model      # or: ollama pull qwen2.5:3b
```

This downloads the default model `qwen2.5:3b` (roughly **2 GB**). `qwen2.5:7b` is an
optional, higher-accuracy alternative. Skip this step if you only intend to use the
`hf` backend.

## 4. Configure the environment

Copy the example file and edit the values:

```bash
cp .env.example .env
```

`.env` is gitignored. Variables:

| Variable | Meaning | Default |
| --- | --- | --- |
| `EXTRACTOR_BACKEND` | `ollama` (local) or `hf` (Hugging Face Inference API). | `ollama` |
| `MODEL_NAME` | Model override. For `ollama`, a pulled tag (e.g. `qwen2.5:3b`); for `hf`, a hosted id (e.g. `Qwen/Qwen2.5-7B-Instruct`). | `qwen2.5:3b` |
| `HF_TOKEN` | Hugging Face access token (Read scope). **Required only when** `EXTRACTOR_BACKEND=hf`. | _empty_ |
| `OLLAMA_HOST` | Optional override of the Ollama server location. | `http://localhost:11434` |

## 5. Run the app

```bash
make run             # or: streamlit run app/streamlit_app.py
```

Streamlit prints a local URL (typically <http://localhost:8501>); open it in a browser.
Type a controller **instruction** and a pilot **readback**, and the app returns a
verdict (MATCH, or DISCREPANCY with the specific problems found).

## 6. Run the evaluation

```bash
make eval            # or: python eval/run_eval.py
```

This runs the comparator over the 50 labelled cases in
`eval/data/atc_readback_test_set.csv` using the configured backend, and writes results
to **`eval/results/`**:

- `metrics.md` / `metrics.json` — precision, recall, F1, false-alarm rate, verdict
  accuracy, per-category recall, and a confusion matrix.
- `predictions.csv` — per-case predicted vs. expected (full audit trail).
- `failures.md` — misclassified cases for failure-mode analysis.

Open `eval/results/metrics.md` for the reported figures. Re-run `make eval` to
regenerate them.

## 7. Run the tests

```bash
make test            # or: pytest
```

`tests/test_compare.py` unit-tests the deterministic comparator only — no LLM call and
no token required, so these tests run anywhere (including CI).

## 8. Deploy to Streamlit Community Cloud

The hosted demo uses the `hf` backend because the cloud free tier (1 GB) cannot run a
local model. A human must perform the one-time GitHub OAuth sign-in and Deploy click.

1. Go to <https://share.streamlit.io> and **sign in with GitHub**.
2. Click **New app** and select the `janwejchert/NLP` repository and branch.
3. Set the main file path to **`app/streamlit_app.py`**.
4. Open **Advanced settings → Secrets** and add:

   ```toml
   EXTRACTOR_BACKEND = "hf"
   HF_TOKEN = "<your-hugging-face-read-token>"
   ```

5. Click **Deploy**.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `could not connect` / connection refused to Ollama | The Ollama app is not running. | Start the Ollama app, then retry. Confirm the daemon is up (default `http://localhost:11434`). |
| Model error / model not found at extraction time | The local model was never pulled. | Run `make pull-model` (or `ollama pull qwen2.5:3b`). |
| Custom Ollama port/host ignored | App points at the default location. | Set `OLLAMA_HOST` in `.env` to your server URL. |
| `The HF backend needs a token...` | `EXTRACTOR_BACKEND=hf` but `HF_TOKEN` is empty. | Add a free Read-scope token to `HF_TOKEN` in `.env` (or to Streamlit Secrets). |
| `The 'ollama' package is required...` | Dependencies not installed. | Run `make setup` (or `pip install -r requirements.txt -r requirements-dev.txt && pip install -e .`). |
| `python3` reports < 3.10 | Wrong interpreter on PATH. | Install Python 3.10+ and recreate `.venv` (the team uses 3.13). |
