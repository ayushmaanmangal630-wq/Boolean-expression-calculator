# LOGICFLOW — Python edition

A Python web application for Boolean expression simplification, built with Streamlit. The parser and minimizer are in `logic_engine.py`, separate from the UI.

## Run locally

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Push this folder to a GitHub repository and deploy it on Streamlit Community Cloud, choosing this repository and `app.py` as the app entry point. Keep `requirements.txt` at the project root that you deploy. The host runs the app, so you do not need to keep your own computer on. You can share the hosted public URL while the app remains deployed. Calculation history is session-local and may reset when the host restarts the app.

## Supported operations

AND (`AB`, `A·B`, `A&B`), OR (`+`, `∨`), NOT (`'`, `!`, `~`, `¬`), XOR (`⊕`), XNOR (`⊙`), NAND (`↑`), NOR (`↓`), parentheses, constants `0` and `1`, and implicit AND. Exact Quine–McCluskey minimization is limited to 8 variables. The main result compares equivalent SOP/POS forms by parsed operator count and verifies the selected expression against every truth-table row. A constant such as `0` is shown when the function is actually constant; forcing a nonconstant result would be incorrect. The solution insight displays De Morgan's law for an outer complement over AND/OR.

Don't-care indices may be entered as comma-separated decimal minterms. The expression itself provides fully specified values, so entries already defined by the expression do not override those values.
