# GTM Campaign Overview

Simpel Streamlit-app med overblik over GTM-kampagner fra syv værktøjer:

**Customer.io · Lemlist · Instantly · Smartlead · Apollo · Clay · HubSpot**

## Sådan virker UI

1. **Forside (Integrationer)** — kort-grid med alle værktøjer (kampagner i alt + aktive)
2. **Åbn et kort** — kampagnetabel for det værktøj (status, open/reply rate, leads)
3. **← Tilbage** — tilbage til forsiden (ingen filtre på forsiden)

Standard er **Dummy data** (ingen API-kald). Thin Live-klienter findes for Customer.io og Lemlist; de øvrige er dummy indtil videre.

## Kør lokalt

```bash
pip install -r requirements.txt
cp .env.example .env   # kun nødvendigt til Live APIs
streamlit run app.py
```

## Streamlit Community Cloud

Efter push: vent på auto-redeploy, eller **Reboot app** i Cloud-dashboardet hvis den hænger.

Hvis app-settings tillader det, vælg **Python 3.12** (mere stabilt end 3.14 på Cloud). Appen bruger `st.table(list[dict])` uden pandas/pyarrow.

## Secrets

Læg aldrig rigtige API-nøgler i git. Brug `.env` lokalt (se `.env.example`) eller Streamlit Cloud secrets.
