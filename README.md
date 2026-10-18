# GTM Campaign Overview

Simpel Streamlit-app med overblik over Customer.io og Lemlist-kampagner.

## Sådan virker UI

1. **Overblik** — to integrations-kort med antal kampagner og antal aktive
2. **Klik et kort** — kampagnetabel for det værktøj (status + metrics)
3. **← Overblik** — tilbage til forsiden (ingen store filtre på forsiden)

Standard er **Dummy data** (ingen API-kald). Live API-klienter er i koden, men bruges kun hvis du aktivt vælger dem.

## Kør lokalt

```bash
pip install -r requirements.txt
cp .env.example .env   # kun nødvendigt til Live APIs
streamlit run app.py
```

## Streamlit Community Cloud

Efter push: **Reboot app** i Cloud-dashboardet, så den henter den nye `requirements.txt`.

Hvis app-settings tillader det, vælg **Python 3.12** (mere stabilt end 3.14 på Cloud). Appen er skrevet til at køre uden pandas/pyarrow-pins, også hvis Cloud bliver på 3.14.

## Secrets

Læg aldrig rigtige API-nøgler i git. Brug `.env` lokalt (se `.env.example`) eller Streamlit Cloud secrets.
