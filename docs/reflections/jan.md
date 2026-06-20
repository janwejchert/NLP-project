# Individual Reflection: Jan

**Role:** App / UI & hosting - repo owner (`app/streamlit_app.py`, Streamlit Cloud deploy, CI, Makefile); author of the analysis notebook (`notebooks/analysis.ipynb`).

## My specific contributions

I built the demo UI in `app/streamlit_app.py`: a dark control-tower "annunciator" theme where a phosphor-green light reads READBACK VERIFIED on a MATCH and a pulsing red CHECK light fires on a discrepancy. I wrote the two-column instruction/readback inputs, the scenario picker (`EXAMPLES`, e.g. "Transposed runway 21 → 12" and a callsign-error case), the field-by-field readout table mapping each `Discrepancy.category` to a styled status strip, and the "Raw extracted fields (JSON)" expander so reviewers can see exactly what the model returned. I wrapped the extractor in `@st.cache_resource` so it loads once per session. I own the GitHub repo, the `.github/workflows/ci.yml` (ruff + pytest on 3.11/3.12), and the Makefile. I deployed the hosted demo on Streamlit Community Cloud, and I authored `notebooks/build_notebook.py`, which generates `analysis.ipynb` end to end: the unit tests, the comparator on worked examples, the live pipeline, the four-run metrics table, the prompt-iteration experiment, the 3B-vs-7B figures, and the failure analysis.

## What I learned (NLP and engineering)

The biggest lesson was that the same code must run in two very different environments. Locally it talks to ollama (`qwen2.5:3b`); on the free Cloud tier, which cannot run a local model, it uses the `hf` backend. I learned that Streamlit Cloud exposes secrets via `st.secrets`, not environment variables, so I wrote `_load_streamlit_secrets()` to bridge `EXTRACTOR_BACKEND` and `HF_TOKEN` into `os.environ`, letting `get_extractor` stay backend-agnostic. On the NLP side, building the notebook taught me to read evaluation as evidence: extraction is the bottleneck, not Vlad's comparator, and the regressed "hardened" run literally doubled the false-alarm rate.

## Challenges and how I handled them

Rendering the field table cleanly was fiddly: the schema's normalization lower-cases callsigns, which looked wrong on screen, so `_display()` falls back to `fields.raw["callsign"]` for the original casing while comparison still uses the normalized form. I also escaped every model-derived string with `html.escape` since I inject raw HTML for the theme. Making the notebook reproducible meant loading committed `eval/results/runs/` artifacts and guarding the live-Ollama cell so it runs without a model.

## If I did it again

I'd add a Playwright smoke test in CI that loads an example and asserts the verdict, and surface model latency in the status bar. I'd also cache HF responses to soften free-tier rate limits during the demo.

## Use of AI tools (personal note)

I used an AI assistant to draft CSS for the annunciator theme and to explain Streamlit's secrets model, but I verified every claim by deploying to Cloud and watching the `hf` backend actually run. I confirmed the notebook regenerates by running `python notebooks/build_notebook.py` then `nbconvert --execute` and checking the numbers matched our committed metrics.
