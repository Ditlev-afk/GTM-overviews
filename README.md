# GTM hub · Integrationer & Noter

Keen-inspireret Streamlit-hub til partnerships/GTM-arbejde.

**Customer.io · Lemlist · Instantly · Smartlead · Apollo · Clay · HubSpot**

## Sådan virker UI

1. **Sidebar** — skift mellem **Integrationer** og **Noter & Eksperimenter** (Dummy er standard)
2. **Forside** — “Hvad kører lige nu” (aktive kampagner) + kort-grid for alle værktøjer
3. **Åbn et kort** — kampagnetabel (status, open/reply rate, leads) + vælg/åbn en kampagne
4. **Kampagne-detalje** — metrics + note (hypotese / læring / næste skridt) i sessionen
5. **Noter & Eksperimenter** — samlet overblik med søg/filter; knap tilbage til kampagnen

Standard er **Dummy data** (ingen API-kald). Thin Live-klienter findes for Customer.io og Lemlist.

## Kør lokalt

```bash
pip install -r requirements.txt
cp .env.example .env   # kun nødvendigt til Live APIs
streamlit run app.py
```

## Streamlit Community Cloud

Efter push: vent på auto-redeploy, eller **Reboot app** i Cloud-dashboardet hvis den hænger.

Hvis app-settings tillader det, vælg **Python 3.12**. Appen bruger `st.table(list[dict])` uden pandas/pyarrow.

## Secrets

Læg aldrig rigtige API-nøgler i git. Brug `.env` lokalt (se `.env.example`) eller Streamlit Cloud secrets.
