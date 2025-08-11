# ChartSight AI — Streamlit Cloud Deploy (v2)

Deploy on Streamlit Community Cloud with no terminal.

## Deploy
1) Create a new GitHub repo and upload all files in this folder to the repo root.
2) Go to https://share.streamlit.io → New app → select your repo & branch → set main file to `app.py`.
3) Click Deploy. You'll get a public URL when it finishes.

Notes:
- Uses `opencv-python-headless` (no libGL needed).
- If OCR isn't available, set Chart Price Min/Max in the sidebar to calibrate.
- Educational use only. Not financial advice.