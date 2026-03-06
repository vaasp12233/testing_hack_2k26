# AI Fraud Shield Pro (Streamlit)

This folder contains the Streamlit app entrypoint: `streamlit_app.py`.

## Run locally

1. Create/activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run streamlit_app.py
```

## Model files (optional)

If you have trained models, place them in a `models/` folder next to `streamlit_app.py`:

- `models/model_risk.pkl`
- `models/tfidf_vectorizer.pkl`
- (optional) `models/label_encoder.pkl`
- (optional) `models/model_type.pkl`

If model files are missing, the app still works in **heuristic fallback mode** and will show a warning in the sidebar.

