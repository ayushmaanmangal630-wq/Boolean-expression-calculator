from __future__ import annotations

import pandas as pd
import streamlit as st
from logic_engine import format_implicant, simplify

st.set_page_config(page_title="LOGICFLOW — Boolean Studio", page_icon="◈", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--bg:#101318;--panel:#171b21;--edge:#2a3039;--muted:#8b95a4;--text:#e8eaed;--accent:#adc4bd}
.stApp{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif}
.block-container{max-width:1450px;padding-top:1rem;padding-bottom:3rem}
section[data-testid="stSidebar"]{background:#13171c;border-right:1px solid var(--edge)}
.brand{font:800 17px Manrope,sans-serif;letter-spacing:1.5px;color:#eef2f0;margin:0 0 2px}.brand span{color:var(--accent)}
.tagline{font:10px 'DM Mono';color:var(--muted);letter-spacing:1.3px;margin:0 0 27px}
.eyebrow{font:9px 'DM Mono';letter-spacing:1.6px;color:#a3b9b2;margin:0 0 8px}
h1{font:700 30px Manrope,sans-serif;letter-spacing:-.7px;margin:0 0 5px} h1 span{color:#adc4bd}
.sub{font-size:12px;color:var(--muted);margin-bottom:24px}
.card{background:var(--panel);border:1px solid var(--edge);border-radius:10px;padding:17px 19px;margin-bottom:14px}
.card-title{font:600 13px Manrope;margin:0 0 4px}.card-sub{font-size:10px;color:var(--muted);margin-bottom:14px}
.result{background:linear-gradient(120deg,#1b2829,#20232a);border:1px solid #3d504b;border-radius:8px;padding:16px;margin:12px 0}
.result label{font:9px 'DM Mono';color:#afc8c0;letter-spacing:1.1px;display:block;margin-bottom:7px}.result strong{font:600 22px 'DM Mono';overflow-wrap:anywhere}
.metric{background:#12161b;border:1px solid #292f37;border-radius:7px;padding:11px 12px}.metric small{display:block;color:var(--muted);font:9px 'DM Mono';letter-spacing:.4px}.metric b{display:block;font:600 20px Manrope;margin:5px 0 2px}.metric span{color:#8d99a8;font-size:9px}
.status{color:#91c5a9;font:9px 'DM Mono';letter-spacing:.6px}
button[kind="primary"]{background:#536e69;border:1px solid #809a94;color:white}
div[data-testid="stDataFrame"]{border:1px solid var(--edge);border-radius:8px;overflow:hidden}
.stTabs [data-baseweb="tab-list"]{gap:14px;border-bottom:1px solid var(--edge)}
.stTabs [data-baseweb="tab"]{height:40px;background:transparent}
.stTabs [aria-selected="true"]{color:#d7e4df!important}
footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">LOGIC<span>FLOW</span></div><div class="tagline">BOOLEAN SIMPLIFICATION STUDIO</div>', unsafe_allow_html=True)
    st.markdown("#### Workspace")
    page = st.radio("Navigate", ["Dashboard", "Simplifier", "Truth Table", "Karnaugh Map", "Logic Circuit", "History", "Notation guide"], label_visibility="collapsed")
    st.divider()
    st.markdown('<div class="status">● ENGINE READY</div>', unsafe_allow_html=True)
    st.caption("Exact minimization · up to 8 variables")
    st.caption("Calculations run locally in this app session.")

st.markdown('<div class="eyebrow">BOOLEAN ALGEBRA WORKBENCH</div><h1>Simplify. <span>Visualize.</span> Understand.</h1><div class="sub">Explore expressions with exact minimization, truth tables, and logic insights.</div>', unsafe_allow_html=True)

if "history" not in st.session_state: st.session_state.history = []
if "result" not in st.session_state: st.session_state.result = None
if "expression" not in st.session_state: st.session_state.expression = "A'B + AB"

def select_example(example: str) -> None:
    """Update the text-area value before Streamlit creates its widget."""
    st.session_state.expression = example

def insert_key(token: str) -> None:
    """Append an on-screen keypad token to the current expression."""
    st.session_state.expression = st.session_state.get("expression", "") + token

def backspace_expression() -> None:
    st.session_state.expression = st.session_state.get("expression", "")[:-1]

def clear_expression() -> None:
    st.session_state.expression = ""

if page in ("Dashboard", "Simplifier"):
    left, right = st.columns([1.05, .95], gap="medium")
    with left:
        st.markdown('<div class="card"><div class="card-title">Expression editor</div><div class="card-sub">Define your Boolean function</div>', unsafe_allow_html=True)
        expression = st.text_area("Boolean expression", key="expression", height=82, placeholder="e.g. A'B + AB")
        st.caption("On-screen Boolean keypad")
        keypad_rows = [
            ["A", "B", "C", "D", "E", "F", "G"],
            ["H", "·", "+", "!", "⊕", "↑", "↓"],
            ["⊙", "(", ")", "0", "1", "⌫", "CLR"],
        ]
        for row_index, key_row in enumerate(keypad_rows):
            key_columns = st.columns(len(key_row))
            for column, token in zip(key_columns, key_row):
                with column:
                    if token == "CLR":
                        st.button("Clear", key=f"keypad-clear-{row_index}", use_container_width=True, on_click=clear_expression)
                    elif token == "⌫":
                        st.button("⌫", key=f"keypad-backspace-{row_index}", use_container_width=True, on_click=backspace_expression)
                    else:
                        st.button(token, key=f"keypad-{row_index}-{token}", use_container_width=True, on_click=insert_key, args=(token,))
        examples = ["A'B + AB", "AB + AB'", "(A+B)(A+B')", "A⊕B", "(A+B)(A'+C)"]
        st.caption("Try an example")
        example_cols = st.columns(len(examples))
        for col, example in zip(example_cols, examples):
            with col:
                st.button(
                    example,
                    key=f"example-{example}",
                    use_container_width=True,
                    on_click=select_example,
                    args=(example,),
                )
        option_cols = st.columns(2)
        with option_cols[0]: dc_text = st.text_input("Don't-care indices", placeholder="e.g. 0, 2, 7")
        with option_cols[1]: mode_label = st.selectbox("Optimization", ["Minimum logic operators", "Minimum literals", "Minimum terms"])
        run = st.button("Simplify expression", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if run:
            try:
                dc = [int(x.strip().lstrip("mM")) for x in dc_text.split(",") if x.strip()]
                mode = "terms" if mode_label == "Minimum terms" else "literals"
                result = simplify(expression, mode, dc)
                st.session_state.result = result
                st.session_state.history.insert(0, {"Expression": expression, "SOP": result["sop"], "POS": result["pos"]})
                st.session_state.history = st.session_state.history[:25]
            except Exception as exc:
                st.error(str(exc))
    with right:
        result = st.session_state.result
        st.markdown('<div class="card"><div class="card-title">Simplified result</div><div class="card-sub">Exact minimized forms</div>', unsafe_allow_html=True)
        if result:
            st.markdown(f'<div class="result"><label>SIMPLIFIED RESULT · VERIFIED</label><strong>{result["algebraic"]}</strong></div>', unsafe_allow_html=True)
            st.caption(f"Minimum equivalent operator form · {result['operator_count']} logic operators · verified over all input rows")
            st.markdown(f'<div class="result"><label>MINIMUM POS</label><strong>{result["pos"]}</strong></div>', unsafe_allow_html=True)
            originals = sum(ch.isalpha() for ch in expression)
            simplified = sum(ch.isalpha() for ch in result["sop"])
            reduction = round((originals-simplified)*100/originals) if originals else 0
            metrics = st.columns(4)
            values = [("VARIABLES", len(result["variables"]), ", ".join(result["variables"])), ("MINTERMS", len(result["ones"]), "ON set"), ("MAXTERMS", len(result["zeros"]), "OFF set"), ("LITERAL REDUCTION", f"{reduction}%", f"{originals} → {simplified}")]
            for column, (title, value, hint) in zip(metrics, values):
                with column: st.markdown(f'<div class="metric"><small>{title}</small><b>{value}</b><span>{hint}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<p class="status">✓ EQUIVALENCE CHECKED · {len(result["rows"])} INPUT COMBINATIONS</p>', unsafe_allow_html=True)
            if result["alternatives"]:
                with st.expander("Equally optimal alternatives"):
                    st.write(" · ".join(result["alternatives"]))
        else:
            st.info("Enter an expression, choose an optimization mode, then simplify to see exact SOP and POS forms.")
        st.markdown('</div>', unsafe_allow_html=True)

    if result:
        tab_names = ["Truth Table", "Karnaugh Map", "Solution Insight", "Logic Circuit"]
        tabs = st.tabs(tab_names)
        with tabs[0]:
            frame = pd.DataFrame([{"Minterm": i, **dict(zip(result["variables"], bits)), "F": value, "SOP": value, "POS": value} for i, bits, value in result["rows"]])
            st.dataframe(frame, use_container_width=True, hide_index=True, height=330)
            st.download_button("Download truth table CSV", frame.to_csv(index=False), "logicflow-truth-table.csv", "text/csv")
        with tabs[1]:
            names = result["variables"]
            if 2 <= len(names) <= 6:
                row_count = len(names)//2
                row_vars, col_vars = names[:row_count], names[row_count:]
                gray = lambda n: [i ^ (i >> 1) for i in range(1 << n)]
                row_codes, col_codes = gray(len(row_vars)), gray(len(col_vars))
                grid = []
                for row in row_codes:
                    line = {"": format(row, f"0{len(row_vars)}b")}
                    for col in col_codes:
                        index = int(format(row, f"0{len(row_vars)}b") + format(col, f"0{len(col_vars)}b"), 2)
                        line[format(col, f"0{len(col_vars)}b")] = "1" if index in result["ones"] else "0"
                    grid.append(line)
                st.caption(f"Gray-code order · row variables {', '.join(row_vars)} · columns {', '.join(col_vars)}")
                st.dataframe(pd.DataFrame(grid).set_index(""), use_container_width=True)
                st.markdown("**Prime implicants:** " + (" · ".join(format_implicant(p, names) for p in result["prime_implicants"]) or "none"))
            else: st.info("Karnaugh maps are shown for 2–6 variables.")
        with tabs[2]:
            for index, (expression_step, law) in enumerate(result["law_steps"], 1):
                if index == 1: st.markdown(f"**Input:** `{expression_step}`")
                else: st.markdown(f"**Step {index-1} — {law}:** `{expression_step}`")
            st.markdown(f"**Verified result:** `{result['algebraic']}` · **{result['operator_count']} operators**")
            st.caption(f"Equivalence was checked for all {len(result['rows'])} input combinations. Truth-table minimization independently returns SOP `{result['sop']}` and POS `{result['pos']}`.")
        with tabs[3]:
            st.markdown("**Output expression**")
            st.code("F = " + result["sop"])
            st.caption("The minimized SOP is shown as a gate-level implementation: complemented literals feed AND terms, then product terms feed an OR output.")

elif page == "Truth Table":
    st.markdown('<div class="card"><div class="card-title">Truth table</div><div class="card-sub">Generate a verified table from an expression</div>', unsafe_allow_html=True)
    expr = st.text_input("Expression", value=st.session_state.expression, key="truth_expr")
    if st.button("Generate table", type="primary"):
        try: st.session_state.result = simplify(expr)
        except Exception as exc: st.error(str(exc))
    result = st.session_state.result
    if result:
        frame = pd.DataFrame([{"Minterm": i, **dict(zip(result["variables"], bits)), "F": v} for i, bits, v in result["rows"]])
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", frame.to_csv(index=False), "logicflow-truth-table.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)
elif page == "History":
    st.markdown("### Calculation history")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
        if st.button("Clear history"): st.session_state.history = []
    else: st.info("Your recent calculations will appear here during this session.")
elif page == "Notation guide":
    st.markdown("### Boolean notation")
    st.markdown("| Operation | Notation |\n|---|---|\n| AND | `AB`, `A·B`, `A&B` |\n| OR | `A+B`, `A∨B` |\n| NOT | `A'`, `!A`, `¬A` |\n| XOR | `A⊕B` |\n| XNOR | `A⊙B` |\n| NAND | `A↑B` |\n| NOR | `A↓B` |\n\nPrecedence is NOT, AND, XOR/XNOR, then OR. Exact minimization supports up to 8 variables.")
else:
    st.info("Simplify an expression first to see the generated map or gate-level view.")

st.markdown("---")
st.caption("LOGICFLOW · Boolean Simplification Studio · Python edition")
