"""Streamlit UI for the ATC Readback Verifier.

Visual language: a dark control-tower / cockpit-instrument theme — phosphor green
for a clean read-back, caution amber and warning red for problems — so the verdict
reads like an annunciator panel during the live demo.

Run locally:   streamlit run app/streamlit_app.py   (uses the ollama backend)
Hosted (cloud): set EXTRACTOR_BACKEND=hf and HF_TOKEN in the app's secrets.
"""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path

# Make `src/` importable without installing the package (e.g. on Streamlit Cloud).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from atc_verifier import verify  # noqa: E402
from atc_verifier.extract.base import get_extractor  # noqa: E402
from atc_verifier.schema import FIELD_NAMES  # noqa: E402

load_dotenv(ROOT / ".env")


def _load_streamlit_secrets() -> None:
    """Bridge Streamlit Cloud secrets into env vars (they are not set as env vars)."""
    for key in ("EXTRACTOR_BACKEND", "MODEL_NAME", "HF_TOKEN", "OLLAMA_HOST"):
        if os.environ.get(key):  # already set (treat empty string as unset)
            continue
        try:
            value = st.secrets[key]
        except Exception:
            # No secrets file (local run) or key absent — fine; skip this key
            # rather than aborting the whole bridge.
            continue
        if value:
            os.environ[key] = str(value)


_load_streamlit_secrets()

EXAMPLES = {
    "Correct read-back": (
        "Speedbird 245, descend flight level 240, turn left heading 270.",
        "Descend flight level 240, left heading 270, Speedbird 245.",
    ),
    "Wrong altitude (substitution)": (
        "Speedbird 245, descend flight level 240.",
        "Descend flight level 250, Speedbird 245.",
    ),
    "Transposed runway (21 → 12)": (
        "Vueling 38 Lima, line up and wait runway 21.",
        "Line up and wait runway 12, Vueling 38 Lima.",
    ),
    "Omitted item": (
        "Iberia 6020, turn right heading 120, contact Tower 118.7.",
        "Right heading 120, Iberia 6020.",
    ),
    "Callsign error": (
        "Speedbird 245, climb flight level 280.",
        "Climb flight level 280, Speedbird 254.",
    ),
}

FIELD_LABELS = {
    "callsign": "CALLSIGN",
    "altitude": "ALTITUDE",
    "heading": "HEADING",
    "speed": "SPEED",
    "frequency": "FREQUENCY",
    "squawk": "SQUAWK",
    "runway": "RUNWAY",
    "qnh": "QNH",
}

# category -> (row css class, status label)
STATUS = {
    "match": ("ok", "● MATCH"),
    "value_substitution": ("bad", "✕ WRONG VALUE"),
    "digit_transposition": ("bad", "✕ TRANSPOSED"),
    "callsign_error": ("bad", "✕ CALLSIGN"),
    "omission": ("warn", "▽ OMITTED"),
    "added_element": ("warn", "△ ADDED"),
}

CATEGORY_TAG = {
    "value_substitution": "WRONG VALUE",
    "digit_transposition": "TRANSPOSITION",
    "callsign_error": "CALLSIGN ERROR",
    "omission": "OMISSION",
    "added_element": "ADDED ELEMENT",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #070b10;
  --panel: #0e151e;
  --panel-2: #121b26;
  --line: #1d2a38;
  --ink: #cdd9e3;
  --muted: #6f8595;
  --green: #18e3a0;
  --green-dim: #0c8f66;
  --amber: #ffb02e;
  --red: #ff4d5e;
}

.stApp {
  background:
    radial-gradient(900px 420px at 50% -8%, rgba(24,227,160,0.10), transparent 60%),
    repeating-linear-gradient(0deg, rgba(120,160,180,0.035) 0 1px, transparent 1px 34px),
    repeating-linear-gradient(90deg, rgba(120,160,180,0.035) 0 1px, transparent 1px 34px),
    var(--bg);
  color: var(--ink);
  font-family: 'IBM Plex Mono', monospace;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 880px; padding-top: 1.4rem; padding-bottom: 4rem; }

h1, h2, h3, h4 { font-family: 'Chakra Petch', sans-serif !important; letter-spacing: .04em; }

/* ---- hero ---- */
.hero {
  position: relative; overflow: hidden;
  border: 1px solid var(--line); border-left: 3px solid var(--green);
  border-radius: 10px; padding: 22px 26px; margin-bottom: 26px;
  background:
    linear-gradient(180deg, rgba(24,227,160,0.05), transparent),
    var(--panel);
}
.hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0 1px, transparent 1px 4px);
}
.hero-tag {
  font-size: 11px; letter-spacing: .22em; color: var(--green);
  display: inline-flex; align-items: center; gap: 8px; margin-bottom: 10px;
}
.dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 10px var(--green); animation: pulse 1.8s infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .25; } }
.hero-title {
  font-family: 'Chakra Petch', sans-serif; font-weight: 700;
  font-size: 34px; letter-spacing: .06em; margin: 0; color: #eaf3f7;
  text-shadow: 0 0 22px rgba(24,227,160,0.20);
}
.hero-sub { color: var(--muted); font-size: 13px; margin: 8px 0 0; max-width: 60ch; }

/* ---- field labels ---- */
.stTextArea label, .stSelectbox label, .stTextInput label {
  font-family: 'IBM Plex Mono', monospace !important;
  text-transform: uppercase; letter-spacing: .14em; font-size: 11px !important;
  color: var(--green) !important;
}
.stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
  background: var(--panel) !important; color: var(--ink) !important;
  border: 1px solid var(--line) !important; border-radius: 8px !important;
  font-family: 'IBM Plex Mono', monospace !important;
}
.stTextArea textarea:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 1px var(--green), 0 0 18px rgba(24,227,160,0.18) !important;
}

/* ---- verify button ---- */
.stButton > button {
  width: 100%; border: 0; border-radius: 8px; padding: .65rem 1rem;
  background: linear-gradient(180deg, var(--green), var(--green-dim));
  color: #04150f; font-family: 'Chakra Petch', sans-serif; font-weight: 700;
  letter-spacing: .18em; text-transform: uppercase; transition: all .15s ease;
}
.stButton > button:hover {
  box-shadow: 0 0 24px rgba(24,227,160,0.45); transform: translateY(-1px);
  color: #04150f;
}

/* ---- sidebar ---- */
[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: var(--green); }

/* ---- annunciator ---- */
.annunciator {
  display: flex; align-items: center; gap: 18px;
  border: 1px solid var(--line); border-radius: 10px; padding: 18px 22px; margin: 6px 0 8px;
  background: var(--panel-2);
}
.annunciator .light {
  width: 16px; height: 16px; border-radius: 50%; flex: none;
}
.annunciator .a-title {
  font-family: 'Chakra Petch', sans-serif; font-weight: 700; font-size: 20px; letter-spacing: .06em;
}
.annunciator .a-sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
.annunciator .a-code {
  margin-left: auto; font-family: 'Chakra Petch', sans-serif; font-weight: 700;
  font-size: 22px; letter-spacing: .12em; padding: 6px 14px; border-radius: 6px;
}
.annunciator.ok { border-color: rgba(24,227,160,0.5); box-shadow: 0 0 30px rgba(24,227,160,0.12) inset; }
.annunciator.ok .light { background: var(--green); box-shadow: 0 0 16px var(--green); }
.annunciator.ok .a-title { color: var(--green); }
.annunciator.ok .a-code { color: var(--green); border: 1px solid var(--green); }
.annunciator.bad { border-color: rgba(255,77,94,0.55); box-shadow: 0 0 30px rgba(255,77,94,0.10) inset; }
.annunciator.bad .light { background: var(--red); box-shadow: 0 0 16px var(--red); animation: pulse 1.1s infinite; }
.annunciator.bad .a-title { color: var(--red); }
.annunciator.bad .a-code { color: var(--red); border: 1px solid var(--red); }

/* ---- discrepancy strips ---- */
.disc {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  border: 1px solid var(--line); border-left: 3px solid var(--amber);
  border-radius: 7px; padding: 10px 14px; margin: 8px 0; background: var(--panel);
}
.disc .cat {
  font-size: 10.5px; letter-spacing: .12em; color: #04150f; background: var(--amber);
  padding: 3px 8px; border-radius: 4px; font-weight: 600;
}
.disc .fld { color: var(--green); text-transform: uppercase; font-size: 12px; letter-spacing: .08em; }
.disc .det { color: var(--ink); font-size: 13px; }

/* ---- field readout table ---- */
.readout-title {
  font-family: 'Chakra Petch', sans-serif; letter-spacing: .14em; text-transform: uppercase;
  font-size: 12px; color: var(--muted); margin: 22px 0 8px;
}
table.readout { width: 100%; border-collapse: collapse; font-size: 13px; }
table.readout th {
  text-align: left; color: var(--muted); font-weight: 500; text-transform: uppercase;
  letter-spacing: .12em; font-size: 10.5px; padding: 6px 10px; border-bottom: 1px solid var(--line);
}
table.readout td { padding: 9px 10px; border-bottom: 1px solid rgba(29,42,56,0.6); }
table.readout td.fld { color: var(--ink); letter-spacing: .05em; }
table.readout td.val { color: var(--muted); }
table.readout td.st { text-align: right; white-space: nowrap; font-weight: 600; letter-spacing: .04em; }
tr.ok td.st { color: var(--green); }
tr.ok td.val.match { color: var(--ink); }
tr.bad td.st { color: var(--red); }
tr.bad td.val { color: var(--red); }
tr.warn td.st { color: var(--amber); }
tr.warn td.val { color: var(--amber); }

/* ---- status bar ---- */
.statusbar {
  margin-top: 26px; padding-top: 12px; border-top: 1px solid var(--line);
  display: flex; gap: 22px; flex-wrap: wrap; color: var(--muted);
  font-size: 11px; letter-spacing: .1em; text-transform: uppercase;
}
.statusbar b { color: var(--green); font-weight: 600; }
</style>
"""


@st.cache_resource(show_spinner=False)
def _extractor(backend: str, model: str):
    kwargs = {"model": model} if model else {}
    return get_extractor(backend, **kwargs)


def _hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-content">
            <div class="hero-tag"><span class="dot"></span>SYSTEM ONLINE · READBACK MONITOR</div>
            <h1 class="hero-title">ATC READBACK VERIFIER</h1>
            <p class="hero-sub">Cross-checks a pilot read-back against the controller's
            clearance, item by item, and flags every discrepancy before it becomes an incident.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _display(fields, name: str) -> str:
    """Readable value for the readout. Callsign shows its original casing (the
    comparator works on a normalized lower-case form, which looks odd on screen)."""
    if fields.get(name) is None:
        return "—"
    if name == "callsign":
        raw = fields.raw.get("callsign")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return fields.human(name)


def _field_rows(result):
    disc = {d.field: d.category for d in result.verdict.discrepancies}
    inst, rb = result.instruction_fields, result.readback_fields
    rows = []
    for name in FIELD_NAMES:
        if inst.get(name) is None and rb.get(name) is None:
            continue
        cat = disc.get(name, "match")
        cls, label = STATUS.get(cat, ("warn", cat.upper()))
        rows.append(
            {
                "field": FIELD_LABELS[name],
                "inst": _display(inst, name),
                "rb": _display(rb, name),
                "cls": cls,
                "label": label,
                "is_match": cat == "match",
            }
        )
    return rows


def _render_result(result) -> None:
    v = result.verdict
    if v.is_match:
        st.markdown(
            """
            <div class="annunciator ok">
              <div class="light"></div>
              <div>
                <div class="a-title">READBACK VERIFIED</div>
                <div class="a-sub">All required items match the controller's instruction.</div>
              </div>
              <div class="a-code">MATCH</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        n = len(v.discrepancies)
        st.markdown(
            f"""
            <div class="annunciator bad">
              <div class="light"></div>
              <div>
                <div class="a-title">DISCREPANCY DETECTED</div>
                <div class="a-sub">{n} issue(s) found — verify before transmitting.</div>
              </div>
              <div class="a-code">CHECK</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        strips = []
        for d in v.discrepancies:
            tag = CATEGORY_TAG.get(d.category, d.category.replace("_", " ").upper())
            strips.append(
                f'<div class="disc"><span class="cat">{html.escape(tag)}</span>'
                f'<span class="fld">{html.escape(d.field)}</span>'
                f'<span class="det">{html.escape(d.detail)}</span></div>'
            )
        st.markdown("".join(strips), unsafe_allow_html=True)

    # Field-by-field readout
    rows = _field_rows(result)
    body = []
    for r in rows:
        val_match_cls = "val match" if r["is_match"] else "val"
        body.append(
            f'<tr class="{r["cls"]}">'
            f'<td class="fld">{html.escape(r["field"])}</td>'
            f'<td class="{val_match_cls}">{html.escape(r["inst"])}</td>'
            f'<td class="{val_match_cls}">{html.escape(r["rb"])}</td>'
            f'<td class="st">{html.escape(r["label"])}</td></tr>'
        )
    st.markdown('<div class="readout-title">Field-by-field readout</div>', unsafe_allow_html=True)
    st.markdown(
        '<table class="readout"><thead><tr><th>Field</th><th>Instruction</th>'
        '<th>Read-back</th><th>Status</th></tr></thead><tbody>'
        + "".join(body)
        + "</tbody></table>",
        unsafe_allow_html=True,
    )

    with st.expander("Raw extracted fields (JSON)"):
        c1, c2 = st.columns(2)
        c1.caption("Instruction")
        c1.json(result.instruction_fields.raw or {})
        c2.caption("Read-back")
        c2.json(result.readback_fields.raw or {})


def main() -> None:
    st.set_page_config(page_title="ATC Readback Verifier", page_icon="🛫", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    _hero()

    with st.sidebar:
        st.header("Console")
        # Default to hf when a token is present (the hosted-cloud case, which
        # cannot run a local Ollama), else ollama for local development.
        default_backend = os.getenv("EXTRACTOR_BACKEND") or (
            "hf" if os.getenv("HF_TOKEN") else "ollama"
        )
        backend = st.selectbox(
            "Extraction backend",
            options=["ollama", "hf"],
            index=0 if default_backend == "ollama" else 1,
            help="ollama = local model; hf = Hugging Face Inference API (needs HF_TOKEN).",
        )
        model = st.text_input(
            "Model override",
            value=os.getenv("MODEL_NAME", ""),
            placeholder="qwen2.5:3b  ·  Qwen/Qwen2.5-7B-Instruct",
        )
        st.markdown("---")
        st.subheader("Scenarios")
        choice = st.selectbox(
            "Load an example", ["—"] + list(EXAMPLES.keys()), key="example_choice"
        )
        # Apply an example only when the selection actually changes. Otherwise the
        # rerun triggered by the Verify button would re-apply the example and wipe
        # any edits the user made after loading it.
        if choice != "—" and choice != st.session_state.get("_last_example"):
            st.session_state["_last_example"] = choice
            st.session_state["instruction"], st.session_state["readback"] = EXAMPLES[choice]

    col1, col2 = st.columns(2)
    with col1:
        instruction = st.text_area(
            "Controller instruction",
            key="instruction",
            height=120,
            placeholder="Speedbird 245, climb flight level 280.",
        )
    with col2:
        readback = st.text_area(
            "Pilot read-back",
            key="readback",
            height=120,
            placeholder="Climb flight level 280, Speedbird 245.",
        )

    if st.button("▶ Verify read-back"):
        if not instruction.strip() or not readback.strip():
            st.warning("Enter both an instruction and a read-back.")
            return
        try:
            with st.spinner("Extracting fields and comparing…"):
                extractor = _extractor(backend, model.strip())
                result = verify(instruction, readback, extractor)
        except Exception as exc:
            st.error(f"Could not run the verifier: {exc}")
            if backend == "ollama":
                st.info("Is Ollama running and the model pulled? Try `ollama pull qwen2.5:3b`.")
            else:
                st.info("The HF backend needs a valid HF_TOKEN in the app secrets.")
            return

        # A silent extraction failure (empty / unparseable model output on both
        # sides) yields all-None fields, which the comparator would otherwise
        # report as a confident MATCH — the worst failure mode for a safety check.
        if not result.instruction_fields.raw and not result.readback_fields.raw:
            st.error(
                "Extraction returned no fields — the model may have failed, timed "
                "out, or returned unparseable output. Cannot verify this read-back."
            )
            if backend == "ollama":
                st.info("Is Ollama running and the model pulled? Try `ollama pull qwen2.5:3b`.")
            else:
                st.info("The HF backend needs a valid HF_TOKEN in the app secrets.")
            return

        _render_result(result)
        backend_name = getattr(extractor, "name", backend)
        model_name = getattr(extractor, "model", model or "default")
        st.markdown(
            f'<div class="statusbar"><span>EXTRACTOR · <b>{html.escape(backend_name)}</b></span>'
            f'<span>MODEL · <b>{html.escape(str(model_name))}</b></span>'
            f'<span>VERDICT · <b>{html.escape(result.status)}</b></span></div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
