# GTM Analytics Hub

Keen-inspireret Streamlit-hub til partnerships/GTM — data, indsigter og anbefalinger.

**PostHog · Customer.io · Lemlist · Instantly · Smartlead · Apollo · Clay · HubSpot**

## Sidebar

1. **Integrationer** — anbefalings-teaser, “Hvad kører lige nu”, integrations-grid → kampagner → detalje
2. **Analytics** — PostHog-lignende dummy (adoption, drop-off, aktive brugere) + kampagneidéer
3. **Budget** — fordeling + forslag (dummy)
4. **Anbefalinger** — fuld liste (status, værktøj, kobling til kampagne)
5. **Noter** — hypoteser / læringer / næste skridt på tværs af kampagner

Navigation bruger knapper + `on_click` (ikke `st.radio` med `key="nav_section"`).

## Kampagne-flow

1. Åbn et integrationskort → tabel (status, rates, leads, anbefaling-id)
2. Åbn kampagne → metrics + link til anbefaling (`linked_recommendation_id`) + noter i sessionen

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
