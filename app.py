"""
GTM / commercial hub — Streamlit-app (Keen-inspireret) til partnerships & GTM.

Sidebar-navigation:
  • Integrationer  — forside + kampagner + kampagne-detalje med noter
  • Noter & Eksperimenter — samlet overblik med søg/filter

Dummy-data er standard. Thin API-klienter for Customer.io/Lemlist ligger klar
til senere Live-brug — nye værktøjer er kun dummy indtil videre.

Kør lokalt:
  1. pip install -r requirements.txt
  2. cp .env.example .env   # kun hvis du vil prøve Live APIs
  3. streamlit run app.py
"""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

# Indlæs .env fra arbejdsmappen (hvis den findes).
load_dotenv()

# ---------------------------------------------------------------------------
# Konstanter / fælles status-værdier i vores UI
# ---------------------------------------------------------------------------
STATUS_ACTIVE = "active"
STATUS_PAUSE = "pause"
STATUS_DRAFT = "draft"
STATUS_FINISHED = "finished"

# Danske labels til visning i UI
STATUS_LABELS = {
    STATUS_ACTIVE: "Aktiv",
    STATUS_PAUSE: "Pause",
    STATUS_DRAFT: "Draft",
    STATUS_FINISHED: "Afsluttet",
}

# Farvede status-præfikser (emoji) — plain text, no Arrow/dataframe stack
STATUS_DISPLAY = {
    STATUS_ACTIVE: "🟢 Aktiv",
    STATUS_PAUSE: "🟡 Pause",
    STATUS_DRAFT: "⚪ Draft",
    STATUS_FINISHED: "🔵 Afsluttet",
}

SOURCE_CUSTOMERIO = "Customer.io"
SOURCE_LEMLIST = "Lemlist"
SOURCE_INSTANTLY = "Instantly"
SOURCE_SMARTLEAD = "Smartlead"
SOURCE_APOLLO = "Apollo"
SOURCE_CLAY = "Clay"
SOURCE_HUBSPOT = "HubSpot"

# Rækkefølge på forsiden (kort-grid)
ALL_SOURCES = [
    SOURCE_CUSTOMERIO,
    SOURCE_LEMLIST,
    SOURCE_INSTANTLY,
    SOURCE_SMARTLEAD,
    SOURCE_APOLLO,
    SOURCE_CLAY,
    SOURCE_HUBSPOT,
]

# Antal kort pr. række på forsiden
GRID_COLS = 3

# Sidebar-sektioner
NAV_INTEGRATIONER = "Integrationer"
NAV_NOTER = "Noter & Eksperimenter"

# Note-felter (hypoteser / læringer / næste skridt)
NOTE_FIELDS = ("hypothesis", "learning", "next_step")
NOTE_FIELD_LABELS = {
    "hypothesis": "Hypotese",
    "learning": "Læring",
    "next_step": "Næste skridt",
}


# ---------------------------------------------------------------------------
# Dummy-data — bruges når du tester UI uden API-nøgler
# ---------------------------------------------------------------------------
def get_dummy_campaigns() -> list[dict[str, Any]]:
    """Returnerer realistisk dummy-data for alle integrationer."""
    return [
        # --- Customer.io ---
        {
            "name": "Onboarding drip — nye trials",
            "source": SOURCE_CUSTOMERIO,
            "status": STATUS_ACTIVE,
            "sent": 1240,
            "opens": 610,
            "clicks": 188,
            "replies": 42,
            "leads": 980,
            "external_id": "cio-101",
        },
        {
            "name": "Win-back (90 dage inactivity)",
            "source": SOURCE_CUSTOMERIO,
            "status": STATUS_PAUSE,
            "sent": 820,
            "opens": 290,
            "clicks": 74,
            "replies": 19,
            "leads": 640,
            "external_id": "cio-204",
        },
        {
            "name": "Product update — Q4 features",
            "source": SOURCE_CUSTOMERIO,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 120,
            "external_id": "cio-309",
        },
        {
            "name": "Nurture — freemium → paid",
            "source": SOURCE_CUSTOMERIO,
            "status": STATUS_FINISHED,
            "sent": 4500,
            "opens": 2100,
            "clicks": 640,
            "replies": 110,
            "leads": 3200,
            "external_id": "cio-088",
        },
        # --- Lemlist ---
        {
            "name": "Outbound — Nordic SaaS founders",
            "source": SOURCE_LEMLIST,
            "status": STATUS_ACTIVE,
            "sent": 980,
            "opens": 520,
            "clicks": 145,
            "replies": 67,
            "leads": 750,
            "external_id": "lem_abc123",
        },
        {
            "name": "Cold — Agency partners DE/AT",
            "source": SOURCE_LEMLIST,
            "status": STATUS_PAUSE,
            "sent": 410,
            "opens": 155,
            "clicks": 38,
            "replies": 12,
            "leads": 380,
            "external_id": "lem_def456",
        },
        {
            "name": "Sequence draft — webinar follow-up",
            "source": SOURCE_LEMLIST,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 95,
            "external_id": "lem_ghi789",
        },
        {
            "name": "Launch week — invite list",
            "source": SOURCE_LEMLIST,
            "status": STATUS_FINISHED,
            "sent": 1500,
            "opens": 890,
            "clicks": 310,
            "replies": 95,
            "leads": 1100,
            "external_id": "lem_jkl012",
        },
        # --- Instantly ---
        {
            "name": "Instantly — Series A CTOs EU",
            "source": SOURCE_INSTANTLY,
            "status": STATUS_ACTIVE,
            "sent": 2100,
            "opens": 980,
            "clicks": 210,
            "replies": 142,
            "leads": 1850,
            "external_id": "ins_eu_cto_01",
        },
        {
            "name": "Instantly — Warm intro follow-up",
            "source": SOURCE_INSTANTLY,
            "status": STATUS_ACTIVE,
            "sent": 640,
            "opens": 410,
            "clicks": 95,
            "replies": 58,
            "leads": 520,
            "external_id": "ins_warm_02",
        },
        {
            "name": "Instantly — Inbox rotation test",
            "source": SOURCE_INSTANTLY,
            "status": STATUS_PAUSE,
            "sent": 300,
            "opens": 90,
            "clicks": 12,
            "replies": 4,
            "leads": 280,
            "external_id": "ins_rot_03",
        },
        {
            "name": "Instantly — Q1 copy A/B draft",
            "source": SOURCE_INSTANTLY,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 150,
            "external_id": "ins_ab_04",
        },
        # --- Smartlead ---
        {
            "name": "Smartlead — PLG self-serve upsell",
            "source": SOURCE_SMARTLEAD,
            "status": STATUS_ACTIVE,
            "sent": 1750,
            "opens": 720,
            "clicks": 180,
            "replies": 96,
            "leads": 1400,
            "external_id": "sl_plg_01",
        },
        {
            "name": "Smartlead — Partner channel outreach",
            "source": SOURCE_SMARTLEAD,
            "status": STATUS_PAUSE,
            "sent": 520,
            "opens": 180,
            "clicks": 40,
            "replies": 15,
            "leads": 480,
            "external_id": "sl_partner_02",
        },
        {
            "name": "Smartlead — Event RSVP chase",
            "source": SOURCE_SMARTLEAD,
            "status": STATUS_FINISHED,
            "sent": 890,
            "opens": 510,
            "clicks": 160,
            "replies": 72,
            "leads": 800,
            "external_id": "sl_event_03",
        },
        {
            "name": "Smartlead — Multi-inbox draft",
            "source": SOURCE_SMARTLEAD,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 220,
            "external_id": "sl_draft_04",
        },
        # --- Apollo ---
        {
            "name": "Apollo — VP Sales US mid-market",
            "source": SOURCE_APOLLO,
            "status": STATUS_ACTIVE,
            "sent": 1320,
            "opens": 540,
            "clicks": 120,
            "replies": 61,
            "leads": 1100,
            "external_id": "apl_vps_01",
        },
        {
            "name": "Apollo — Intent: hiring RevOps",
            "source": SOURCE_APOLLO,
            "status": STATUS_ACTIVE,
            "sent": 760,
            "opens": 310,
            "clicks": 85,
            "replies": 39,
            "leads": 690,
            "external_id": "apl_intent_02",
        },
        {
            "name": "Apollo — Sequence paused (bounce)",
            "source": SOURCE_APOLLO,
            "status": STATUS_PAUSE,
            "sent": 210,
            "opens": 55,
            "clicks": 8,
            "replies": 2,
            "leads": 200,
            "external_id": "apl_bounce_03",
        },
        {
            "name": "Apollo — New ICP draft",
            "source": SOURCE_APOLLO,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 340,
            "external_id": "apl_icp_04",
        },
        # --- Clay ---
        {
            "name": "Clay — Enrich + push to Instantly",
            "source": SOURCE_CLAY,
            "status": STATUS_ACTIVE,
            "sent": 900,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 900,
            "external_id": "clay_enrich_01",
        },
        {
            "name": "Clay — Lookalike: closed-won accounts",
            "source": SOURCE_CLAY,
            "status": STATUS_ACTIVE,
            "sent": 450,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 450,
            "external_id": "clay_lal_02",
        },
        {
            "name": "Clay — Waterfall email find (paused)",
            "source": SOURCE_CLAY,
            "status": STATUS_PAUSE,
            "sent": 1200,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 1200,
            "external_id": "clay_wf_03",
        },
        {
            "name": "Clay — Scraping table draft",
            "source": SOURCE_CLAY,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 80,
            "external_id": "clay_draft_04",
        },
        # --- HubSpot ---
        {
            "name": "HubSpot — MQL nurture (email)",
            "source": SOURCE_HUBSPOT,
            "status": STATUS_ACTIVE,
            "sent": 3200,
            "opens": 1450,
            "clicks": 420,
            "replies": 55,
            "leads": 2800,
            "external_id": "hs_mql_01",
        },
        {
            "name": "HubSpot — Demo no-show recovery",
            "source": SOURCE_HUBSPOT,
            "status": STATUS_ACTIVE,
            "sent": 480,
            "opens": 260,
            "clicks": 95,
            "replies": 38,
            "leads": 420,
            "external_id": "hs_noshow_02",
        },
        {
            "name": "HubSpot — Newsletter pause (Q4)",
            "source": SOURCE_HUBSPOT,
            "status": STATUS_PAUSE,
            "sent": 5600,
            "opens": 2100,
            "clicks": 380,
            "replies": 22,
            "leads": 5100,
            "external_id": "hs_news_03",
        },
        {
            "name": "HubSpot — Lifecycle score draft",
            "source": SOURCE_HUBSPOT,
            "status": STATUS_DRAFT,
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "leads": 0,
            "external_id": "hs_score_04",
        },
        {
            "name": "HubSpot — Customer success check-in",
            "source": SOURCE_HUBSPOT,
            "status": STATUS_FINISHED,
            "sent": 1100,
            "opens": 680,
            "clicks": 190,
            "replies": 84,
            "leads": 950,
            "external_id": "hs_cs_05",
        },
    ]


def get_seed_notes() -> dict[str, dict[str, str]]:
    """
    Forudfyldte noter på udvalgte kampagner (dummy).

    Nøgle = campaign external_id. Persisteres i session_state for sessionen.
    """
    return {
        "cio-101": {
            "hypothesis": "Kortere onboarding-mails øger trial→paid i uge 1.",
            "learning": "Åbningsrate OK, men klik falder efter mail 3.",
            "next_step": "Test 3-mail vs 5-mail drip på næste cohort.",
        },
        "lem_abc123": {
            "hypothesis": "Nordiske founders svarer bedre på partner-vinkel end product pitch.",
            "learning": "Reply rate ~7% — bedst på tirsdag/torsdag send.",
            "next_step": "Skalér til 2. bølge med samme subject-line.",
        },
        "ins_eu_cto_01": {
            "hypothesis": "CTO-segment i EU reagerer på infra-cost angle.",
            "learning": "Warm-up af nye inboxe påvirker deliverability negativt.",
            "next_step": "Pause nye domains 5 dage; genoptag med lavere volume.",
        },
        "hs_noshow_02": {
            "hypothesis": "Samme-dags SMS + email hæver rebook-rate efter no-show.",
            "learning": "Email alene giver ~8% rebook; timing vigtigere end copy.",
            "next_step": "Tilføj Slack-alert til AE inden for 30 min.",
        },
        "clay_enrich_01": {
            "hypothesis": "Waterfall-enrich før Instantly løfter reply via bedre emails.",
            "learning": "Catch-all domains skaber støj — filtrér dem fra.",
            "next_step": "Tilføj verification-step i Clay-table før push.",
        },
    }


# ---------------------------------------------------------------------------
# Status-mapping: API-værdier → vores fælles UI-status
# ---------------------------------------------------------------------------
def map_customerio_status(campaign: dict[str, Any]) -> str:
    """Map Customer.io `active` / `state` til vores status-værdier."""
    active = campaign.get("active")
    state = str(campaign.get("state") or "").lower()

    if state in {"draft", "running", "stopped", "completed", "archived"}:
        mapping = {
            "draft": STATUS_DRAFT,
            "running": STATUS_ACTIVE,
            "stopped": STATUS_PAUSE,
            "completed": STATUS_FINISHED,
            "archived": STATUS_FINISHED,
        }
        return mapping[state]

    if active is True:
        return STATUS_ACTIVE
    if active is False:
        return STATUS_PAUSE
    return STATUS_DRAFT


def map_lemlist_status(raw_status: Any) -> str:
    """Map Lemlist-status (running/paused/draft/ended/…) til vores UI-status."""
    if isinstance(raw_status, list):
        statuses = {str(s).lower() for s in raw_status}
    else:
        statuses = {str(raw_status or "").lower()}

    if "running" in statuses:
        return STATUS_ACTIVE
    if "paused" in statuses or "errors" in statuses:
        return STATUS_PAUSE
    if "draft" in statuses:
        return STATUS_DRAFT
    if "ended" in statuses or "archived" in statuses:
        return STATUS_FINISHED
    return STATUS_DRAFT


def _safe_int(value: Any, default: int = 0) -> int:
    """Konverter til int uden at crashe på None / mærkelige typer."""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _rate(part: int, whole: int) -> float | None:
    """Beregn andel (0–1). Returnerer None hvis der ikke er sendt noget."""
    if whole <= 0:
        return None
    return part / whole


def _format_rate(part: int, whole: int) -> str:
    """Vis rate som procent-streng (undgår pandas/Arrow i tabellen)."""
    rate = _rate(part, whole)
    if rate is None:
        return "—"
    return f"{rate * 100:.1f}%"


def _empty_note() -> dict[str, str]:
    """Tom note-struktur for en kampagne."""
    return {field: "" for field in NOTE_FIELDS}


def _note_has_content(note: dict[str, str] | None) -> bool:
    """True hvis mindst ét note-felt er udfyldt."""
    if not note:
        return False
    return any(str(note.get(f, "")).strip() for f in NOTE_FIELDS)


# ---------------------------------------------------------------------------
# Thin API-klienter (kun CIO + Lemlist; andre værktøjer er dummy indtil videre)
# ---------------------------------------------------------------------------
def fetch_customerio_campaigns() -> list[dict[str, Any]]:
    """
    Hent kampagner/automations fra Customer.io App API.

    Endpoint: GET /v1/campaigns
    Auth: Authorization: Bearer <CUSTOMERIO_APP_API_KEY>
    Docs: https://docs.customer.io/integrations/api/app/tag/automations/
    """
    api_key = os.getenv("CUSTOMERIO_APP_API_KEY", "").strip()
    if not api_key:
        st.warning(
            "Customer.io: mangler `CUSTOMERIO_APP_API_KEY` i miljøet / `.env`."
        )
        return []

    region = os.getenv("CUSTOMERIO_REGION", "us").strip().lower()
    base = (
        "https://api-eu.customer.io"
        if region == "eu"
        else "https://api.customer.io"
    )
    url = f"{base}/v1/campaigns"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        st.error(f"Customer.io API-fejl (HTTP {status}): {exc}")
        return []
    except requests.RequestException as exc:
        st.error(f"Customer.io netværksfejl: {exc}")
        return []
    except ValueError as exc:
        st.error(f"Customer.io: kunne ikke parse JSON-svar: {exc}")
        return []

    raw_list = payload.get("campaigns") if isinstance(payload, dict) else payload
    if not isinstance(raw_list, list):
        st.warning(
            "Customer.io: uventet svar-format (forventede en liste af campaigns)."
        )
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue

        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
        sent = (
            item.get("sent")
            or metrics.get("sent")
            or metrics.get("delivered")
            or 0
        )
        opens = item.get("opens") or metrics.get("opened") or metrics.get("opens") or 0
        clicks = (
            item.get("clicks") or metrics.get("clicked") or metrics.get("clicks") or 0
        )
        leads = item.get("leads") or item.get("audience") or sent

        normalized.append(
            {
                "name": item.get("name") or f"Campaign {item.get('id', '?')}",
                "source": SOURCE_CUSTOMERIO,
                "status": map_customerio_status(item),
                "sent": _safe_int(sent),
                "opens": _safe_int(opens),
                "clicks": _safe_int(clicks),
                "replies": _safe_int(item.get("replies") or metrics.get("replied")),
                "leads": _safe_int(leads),
                "external_id": str(item.get("id", "")),
            }
        )

    return normalized


def fetch_lemlist_campaigns() -> list[dict[str, Any]]:
    """
    Hent kampagner fra Lemlist API.

    Endpoint: GET /api/campaigns?version=v2
    Auth: HTTP Basic med tomt brugernavn og API-nøglen som password
          (requests gør det via auth=('', api_key)).
    Docs: https://developer.lemlist.com/api-reference/endpoints/campaigns/get-many-campaigns
    """
    api_key = os.getenv("LEMLIST_API_KEY", "").strip()
    if not api_key:
        st.warning("Lemlist: mangler `LEMLIST_API_KEY` i miljøet / `.env`.")
        return []

    url = "https://api.lemlist.com/api/campaigns"
    params = {"version": "v2", "limit": 100}

    try:
        response = requests.get(
            url,
            params=params,
            auth=("", api_key),
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        st.error(f"Lemlist API-fejl (HTTP {status}): {exc}")
        return []
    except requests.RequestException as exc:
        st.error(f"Lemlist netværksfejl: {exc}")
        return []
    except ValueError as exc:
        st.error(f"Lemlist: kunne ikke parse JSON-svar: {exc}")
        return []

    if isinstance(payload, dict):
        raw_list = payload.get("campaigns") or payload.get("data") or []
    else:
        raw_list = payload

    if not isinstance(raw_list, list):
        st.warning("Lemlist: uventet svar-format (forventede en liste af campaigns).")
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue

        stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}

        sent = (
            item.get("sent")
            or stats.get("sent")
            or metrics.get("sent")
            or 0
        )
        opens = (
            item.get("opens")
            or stats.get("opened")
            or stats.get("opens")
            or metrics.get("opened")
            or 0
        )
        clicks = (
            item.get("clicks")
            or stats.get("clicked")
            or stats.get("clicks")
            or metrics.get("clicked")
            or 0
        )
        replies = (
            item.get("replied")
            or item.get("replies")
            or stats.get("replied")
            or stats.get("replies")
            or metrics.get("replied")
            or 0
        )
        leads = (
            item.get("nbLeads")
            or item.get("leads")
            or stats.get("leads")
            or sent
        )

        normalized.append(
            {
                "name": item.get("name")
                or f"Campaign {item.get('_id') or item.get('id') or '?'}",
                "source": SOURCE_LEMLIST,
                "status": map_lemlist_status(item.get("status")),
                "sent": _safe_int(sent),
                "opens": _safe_int(opens),
                "clicks": _safe_int(clicks),
                "replies": _safe_int(replies),
                "leads": _safe_int(leads),
                "external_id": str(item.get("_id") or item.get("id") or ""),
            }
        )

    return normalized


def load_live_campaigns() -> list[dict[str, Any]]:
    """
    Hent fra CIO + Lemlist (fejl stopper ikke resten).

    Instantly / Smartlead / Apollo / Clay / HubSpot har endnu ingen Live-klienter
    — i Live-mode får du kun CIO/Lemlist indtil videre.
    """
    campaigns: list[dict[str, Any]] = []
    campaigns.extend(fetch_customerio_campaigns())
    campaigns.extend(fetch_lemlist_campaigns())
    return campaigns


def load_campaigns(mode: str) -> list[dict[str, Any]]:
    """Vælg Dummy eller Live og returnér normaliserede kampagner."""
    if mode == "Dummy":
        return get_dummy_campaigns()

    with st.spinner("Henter kampagner fra Customer.io og Lemlist…"):
        campaigns = load_live_campaigns()
    if not campaigns:
        st.warning(
            "Ingen kampagner hentet. Tjek API-nøgler, netværk og fejlbeskeder. "
            "Skift til Dummy for at teste UI'et."
        )
    return campaigns


# ---------------------------------------------------------------------------
# Session-state / navigation
# ---------------------------------------------------------------------------
def _init_session_state() -> None:
    """Sæt defaults én gang pr. browser-session."""
    defaults: dict[str, Any] = {
        "nav_section": NAV_INTEGRATIONER,
        "page": "home",  # home | campaigns | detail
        "selected_source": None,
        "selected_campaign_id": None,
        "campaign_search": "",
        "notes_search": "",
        "notes_source_filter": "Alle",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Seed noter første gang (kopi, så brugeren kan redigere frit i sessionen)
    if "campaign_notes" not in st.session_state:
        seeded = get_seed_notes()
        st.session_state["campaign_notes"] = {
            cid: dict(note) for cid, note in seeded.items()
        }


def _clear_integration_drilldown() -> None:
    """Nulstil kampagne-navigation når man skifter sektion / går hjem."""
    st.session_state["page"] = "home"
    st.session_state["selected_source"] = None
    st.session_state["selected_campaign_id"] = None
    st.session_state["campaign_search"] = ""


def _on_nav_change() -> None:
    """Callback: ryd drill-down når sidebar-sektion skifter."""
    # Radio skriver allerede den nye værdi til nav_section via key=
    _clear_integration_drilldown()
    st.session_state["notes_search"] = ""
    st.session_state["notes_source_filter"] = "Alle"


def _go_to_source(source: str) -> None:
    """Naviger til kampagnelisten for en given integration."""
    st.session_state["nav_section"] = NAV_INTEGRATIONER
    st.session_state["page"] = "campaigns"
    st.session_state["selected_source"] = source
    st.session_state["selected_campaign_id"] = None
    st.session_state["campaign_search"] = ""


def _go_home() -> None:
    """Tilbage til Integrationer-forsiden."""
    _clear_integration_drilldown()


def _go_to_campaign(source: str, campaign_id: str) -> None:
    """Åbn detaljevisning for én kampagne."""
    st.session_state["nav_section"] = NAV_INTEGRATIONER
    st.session_state["page"] = "detail"
    st.session_state["selected_source"] = source
    st.session_state["selected_campaign_id"] = campaign_id


def _go_back_to_campaigns() -> None:
    """Fra detalje → kampagneliste (samme integration)."""
    st.session_state["page"] = "campaigns"
    st.session_state["selected_campaign_id"] = None


def _get_note(campaign_id: str) -> dict[str, str]:
    """Hent (eller opret tom) note for en kampagne i session_state."""
    notes: dict[str, dict[str, str]] = st.session_state.setdefault(
        "campaign_notes", {}
    )
    if campaign_id not in notes:
        notes[campaign_id] = _empty_note()
    # Sikr at alle felter findes
    for field in NOTE_FIELDS:
        notes[campaign_id].setdefault(field, "")
    return notes[campaign_id]


def _find_campaign(
    campaigns: list[dict[str, Any]], campaign_id: str
) -> dict[str, Any] | None:
    """Find kampagne via external_id."""
    for c in campaigns:
        if str(c.get("external_id", "")) == campaign_id:
            return c
    return None


def _source_stats(campaigns: list[dict[str, Any]], source: str) -> dict[str, int]:
    """Antal kampagner + aktive for én integration."""
    rows = [c for c in campaigns if c.get("source") == source]
    active = sum(1 for c in rows if c.get("status") == STATUS_ACTIVE)
    return {"total": len(rows), "active": active}


def _count_active(campaigns: list[dict[str, Any]]) -> int:
    """Antal aktive kampagner på tværs af alle integrationer."""
    return sum(1 for c in campaigns if c.get("status") == STATUS_ACTIVE)


def _inject_light_css() -> None:
    """Minimal CSS så integrationskort føles mere substantielle."""
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding-top: 0.4rem;
            padding-bottom: 0.6rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] h3 {
            margin-bottom: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sider — Integrationer
# ---------------------------------------------------------------------------
def render_integration_card(
    source: str,
    stats: dict[str, int],
    *,
    has_data: bool,
) -> None:
    """Ét integrationskort med metrics + fuld-bredde Åbn-knap."""
    with st.container(border=True):
        st.markdown(f"### {source}")

        m1, m2 = st.columns(2)
        m1.metric("Kampagner i alt", stats["total"])
        m2.metric("Aktive", stats["active"])

        if has_data and stats["total"] > 0:
            st.caption("● OK — data tilgængelig")
        elif has_data:
            st.caption("○ Ingen kampagner endnu")
        else:
            st.caption("○ Ingen data")

        st.write("")  # lidt luft før knappen
        if st.button(
            f"Åbn {source}",
            key=f"open_{source}",
            use_container_width=True,
            type="primary",
        ):
            _go_to_source(source)
            st.rerun()


def render_home(campaigns: list[dict[str, Any]]) -> None:
    """Forside: Integrationer — aktiv-tæller + kort-grid (ingen filtre)."""
    st.title("Integrationer")
    st.caption(
        "GTM-hub · Customer.io, Lemlist, Instantly, Smartlead, "
        "Apollo, Clay og HubSpot"
    )

    # --- Hvad kører lige nu ---
    active_count = _count_active(campaigns)
    with st.container(border=True):
        st.subheader("Hvad kører lige nu")
        st.metric("Aktive kampagner", active_count)
        st.caption(
            "Antal kampagner med status Aktiv på tværs af alle integrationer."
        )

    st.write("")

    # Grid: GRID_COLS kolonner pr. række
    for row_start in range(0, len(ALL_SOURCES), GRID_COLS):
        row_sources = ALL_SOURCES[row_start : row_start + GRID_COLS]
        cols = st.columns(GRID_COLS)
        for idx, source in enumerate(row_sources):
            with cols[idx]:
                stats = _source_stats(campaigns, source)
                render_integration_card(source, stats, has_data=True)


def render_campaigns(campaigns: list[dict[str, Any]], source: str) -> None:
    """Kampagneliste for én integration: tabel + vælg/åbn kampagne."""
    back_col, title_col = st.columns([1, 5], vertical_alignment="center")
    with back_col:
        if st.button("← Tilbage", use_container_width=True, key="back_to_home"):
            _go_home()
            st.rerun()
    with title_col:
        st.title(source)
        st.caption("Kampagner for denne integration — klik ind for noter")

    rows = [c for c in campaigns if c.get("source") == source]

    search = st.text_input(
        "Søg på kampagnenavn",
        key="campaign_search",
        placeholder="Skriv for at filtrere…",
    )
    query = (search or "").strip().lower()
    if query:
        rows = [c for c in rows if query in str(c.get("name", "")).lower()]

    st.subheader(f"Kampagner ({len(rows)})")

    if not rows:
        st.write("Ingen kampagner matcher søgningen.")
        return

    # st.table(list[dict]) — ingen pandas/DataFrame (Cloud Arrow-crash)
    display_rows: list[dict[str, Any]] = []
    for c in rows:
        sent = _safe_int(c.get("sent"))
        opens = _safe_int(c.get("opens"))
        replies = _safe_int(c.get("replies"))
        leads = _safe_int(c.get("leads"), default=sent)
        status_key = str(c.get("status") or STATUS_DRAFT)

        display_rows.append(
            {
                "Kampagnenavn": c.get("name", ""),
                "Status": STATUS_DISPLAY.get(
                    status_key, STATUS_LABELS.get(status_key, status_key)
                ),
                "Open rate": _format_rate(opens, sent),
                "Reply rate": _format_rate(replies, sent),
                "Antal leads": leads,
            }
        )

    st.table(display_rows)

    # Simpel, Cloud-sikker drill-down: selectbox + knap (undgår dataframe-klik)
    st.write("")
    st.markdown("**Åbn en kampagne**")
    options = {
        f"{c.get('name', '')}  ·  {c.get('external_id', '')}": str(
            c.get("external_id", "")
        )
        for c in rows
    }
    labels = list(options.keys())
    chosen_label = st.selectbox(
        "Vælg kampagne",
        options=labels,
        key=f"campaign_pick_{source}",
        label_visibility="collapsed",
    )
    if st.button(
        "Åbn kampagne",
        type="primary",
        key=f"open_campaign_{source}",
        use_container_width=False,
    ):
        campaign_id = options.get(chosen_label or "", "")
        if campaign_id:
            _go_to_campaign(source, campaign_id)
            st.rerun()


def render_campaign_detail(
    campaigns: list[dict[str, Any]], source: str, campaign_id: str
) -> None:
    """Detaljevisning: metrics + note-felter (persisteret i session_state)."""
    campaign = _find_campaign(campaigns, campaign_id)
    if campaign is None or campaign.get("source") != source:
        st.warning("Kampagnen blev ikke fundet. Går tilbage til listen.")
        _go_back_to_campaigns()
        st.rerun()
        return

    back_col, title_col = st.columns([1, 5], vertical_alignment="center")
    with back_col:
        if st.button(
            "← Kampagner", use_container_width=True, key="back_to_campaigns"
        ):
            _go_back_to_campaigns()
            st.rerun()
    with title_col:
        st.title(str(campaign.get("name", "Kampagne")))
        st.caption(f"{source} · {campaign_id}")

    sent = _safe_int(campaign.get("sent"))
    opens = _safe_int(campaign.get("opens"))
    clicks = _safe_int(campaign.get("clicks"))
    replies = _safe_int(campaign.get("replies"))
    leads = _safe_int(campaign.get("leads"), default=sent)
    status_key = str(campaign.get("status") or STATUS_DRAFT)

    # Metrics-række
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Status",
        STATUS_DISPLAY.get(status_key, STATUS_LABELS.get(status_key, status_key)),
    )
    c2.metric("Open rate", _format_rate(opens, sent))
    c3.metric("Reply rate", _format_rate(replies, sent))
    c4.metric("Leads", leads)
    c5.metric("Sent", sent)

    with st.expander("Flere detaljer", expanded=False):
        detail_rows = [
            {
                "Felt": "Kilde",
                "Værdi": source,
            },
            {
                "Felt": "External ID",
                "Værdi": campaign_id,
            },
            {
                "Felt": "Opens",
                "Værdi": opens,
            },
            {
                "Felt": "Clicks",
                "Værdi": clicks,
            },
            {
                "Felt": "Replies",
                "Værdi": replies,
            },
        ]
        st.table(detail_rows)

    st.divider()
    st.subheader("Noter / eksperiment")
    st.caption(
        "Hypotese, læring og næste skridt — gemmes i sessionen (ikke i database)."
    )

    note = _get_note(campaign_id)

    # Widgets med unikke keys pr. kampagne; synk til session_state ved Gem
    hyp = st.text_area(
        NOTE_FIELD_LABELS["hypothesis"],
        value=note.get("hypothesis", ""),
        key=f"note_hyp_{campaign_id}",
        height=80,
        placeholder="Hvad tester vi?",
    )
    learn = st.text_area(
        NOTE_FIELD_LABELS["learning"],
        value=note.get("learning", ""),
        key=f"note_learn_{campaign_id}",
        height=80,
        placeholder="Hvad lærte vi?",
    )
    nxt = st.text_area(
        NOTE_FIELD_LABELS["next_step"],
        value=note.get("next_step", ""),
        key=f"note_next_{campaign_id}",
        height=80,
        placeholder="Hvad gør vi nu?",
    )

    if st.button("Gem note", type="primary", key=f"save_note_{campaign_id}"):
        st.session_state["campaign_notes"][campaign_id] = {
            "hypothesis": hyp or "",
            "learning": learn or "",
            "next_step": nxt or "",
        }
        st.success("Note gemt i denne session.")
        st.rerun()


# ---------------------------------------------------------------------------
# Side — Noter & Eksperimenter
# ---------------------------------------------------------------------------
def render_notes_page(campaigns: list[dict[str, Any]]) -> None:
    """Samlet overblik over noter på tværs af kampagner med søg/filter."""
    st.title("Noter & Eksperimenter")
    st.caption(
        "Hypoteser, læringer og næste skridt på tværs af alle kampagner."
    )

    notes: dict[str, dict[str, str]] = st.session_state.get("campaign_notes", {})

    # Byg liste af (campaign, note) for noter med indhold
    entries: list[tuple[dict[str, Any], dict[str, str]]] = []
    for c in campaigns:
        cid = str(c.get("external_id", ""))
        note = notes.get(cid) or _empty_note()
        if _note_has_content(note):
            entries.append((c, note))

    # Filtre
    f1, f2 = st.columns([2, 1])
    with f1:
        search = st.text_input(
            "Søg i noter / kampagnenavn",
            key="notes_search",
            placeholder="Fx hypotese, læring, kampagnenavn…",
        )
    with f2:
        source_options = ["Alle", *ALL_SOURCES]
        source_filter = st.selectbox(
            "Integration",
            options=source_options,
            key="notes_source_filter",
        )

    query = (search or "").strip().lower()
    filtered: list[tuple[dict[str, Any], dict[str, str]]] = []
    for c, note in entries:
        if source_filter != "Alle" and c.get("source") != source_filter:
            continue
        if query:
            haystack = " ".join(
                [
                    str(c.get("name", "")),
                    str(c.get("source", "")),
                    str(c.get("external_id", "")),
                    note.get("hypothesis", ""),
                    note.get("learning", ""),
                    note.get("next_step", ""),
                ]
            ).lower()
            if query not in haystack:
                continue
        filtered.append((c, note))

    st.subheader(f"Noter ({len(filtered)})")

    if not filtered:
        st.write(
            "Ingen noter matcher. Åbn en kampagne under Integrationer og tilføj en note."
        )
        return

    for c, note in filtered:
        cid = str(c.get("external_id", ""))
        source = str(c.get("source", ""))
        status_key = str(c.get("status") or STATUS_DRAFT)
        with st.container(border=True):
            head_l, head_r = st.columns([4, 1], vertical_alignment="center")
            with head_l:
                st.markdown(f"**{c.get('name', '')}**")
                st.caption(
                    f"{source} · "
                    f"{STATUS_DISPLAY.get(status_key, status_key)} · "
                    f"{cid}"
                )
            with head_r:
                if st.button(
                    "Åbn",
                    key=f"notes_open_{cid}",
                    use_container_width=True,
                ):
                    _go_to_campaign(source, cid)
                    st.rerun()

            # Vis note-felter kompakt (kun udfyldte)
            for field in NOTE_FIELDS:
                text = str(note.get(field, "")).strip()
                if text:
                    st.markdown(f"*{NOTE_FIELD_LABELS[field]}:* {text}")


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="GTM hub · Integrationer",
        page_icon="📊",
        layout="wide",
    )

    _init_session_state()
    _inject_light_css()

    # Sidebar: sektion-nav + minimal Dummy/Live-toggle
    with st.sidebar:
        st.header("Navigation")
        st.radio(
            "Sektion",
            options=[NAV_INTEGRATIONER, NAV_NOTER],
            key="nav_section",
            on_change=_on_nav_change,
            label_visibility="collapsed",
        )

        st.divider()
        st.header("Indstillinger")
        mode = st.radio(
            "Datakilde",
            options=["Dummy", "Live"],
            index=0,
            help=(
                "Dummy kræver ingen API-nøgler (alle 7 værktøjer). "
                "Live henter kun Customer.io + Lemlist indtil videre."
            ),
        )

    campaigns = load_campaigns(mode)
    section = st.session_state.get("nav_section", NAV_INTEGRATIONER)

    if section == NAV_NOTER:
        render_notes_page(campaigns)
        return

    # --- Integrationer ---
    page = st.session_state.get("page", "home")
    selected = st.session_state.get("selected_source")
    campaign_id = st.session_state.get("selected_campaign_id")

    if page == "detail" and selected in ALL_SOURCES and campaign_id:
        render_campaign_detail(campaigns, selected, str(campaign_id))
    elif page == "campaigns" and selected in ALL_SOURCES:
        render_campaigns(campaigns, selected)
    else:
        st.session_state["page"] = "home"
        render_home(campaigns)


if __name__ == "__main__":
    main()
