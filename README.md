# BTC/USD Momentum Bot (EMA 20/50, 1h, Long-only)

Einfacher Trendfolge-Bot für BTC/USD über Alpaca (Paper), inkl. Streamlit-Dashboard.

## Setup
1) `.env` anhand `.env.example` füllen (Alpaca Paper Keys).  
2) `pip install -r requirements.txt`  
3) Bot starten: `python main.py`  
4) Dashboard: `streamlit run streamlit_app.py` → http://localhost:8501

## Deploy auf Render
- Repo verbinden → Services aus `render.yaml` anlegen (Web + Worker).
- Environment Variables (API Keys) in beiden Services hinterlegen.
- Deploy auslösen.
