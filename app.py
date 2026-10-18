"""
GTM Campaign Overview — Streamlit-app til Magnus.

Navigérbart overblik:
  1. Forside (Integrationer): kort-grid for alle værktøjer
  2. Kampagneside: søgning + tabel med farvet status og nøgletal

Integrationer: Customer.io, Lemlist, Instantly, Smartlead, Apollo, Clay, HubSpot.

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

# Antal kort pr. række på forsiden (2–3 kolonner)
GRID_COLS = 3


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
# Hjælpere til UI
# ---------------------------------------------------------------------------
def _source_stats(campaigns: list[dict[str, Any]], source: str) -> dict[str, int]:
    """Antal kampagner + aktive for én integration."""
    rows = [c for c in campaigns if c.get("source") == source]
    active = sum(1 for c in rows if c.get("status") == STATUS_ACTIVE)
    return {"total": len(rows), "active": active}


def _go_to_source(source: str) -> None:
    """Naviger til kampagnesiden for en given integration."""
    st.session_state["page"] = "campaigns"
    st.session_state["selected_source"] = source


def _go_home() -> None:
    """Tilbage til Integrationer-forsiden."""
    st.session_state["page"] = "home"
    st.session_state["selected_source"] = None
    st.session_state["campaign_search"] = ""


def _inject_light_css() -> None:
    """Minimal CSS så integrationskort føles mere substantielle."""
    st.markdown(
        """
        <style>
        /* Lidt luft mellem kortenes metric-rækker */
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
# Sider
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
    """Forside: Integrationer — alle værktøjer i et kort-grid (ingen filtre)."""
    st.title("Integrationer")
    st.caption(
        "GTM-overblik · Customer.io, Lemlist, Instantly, Smartlead, "
        "Apollo, Clay og HubSpot"
    )

    st.write("")

    # Grid: GRID_COLS kolonner pr. række, wrap resterende kilder
    for row_start in range(0, len(ALL_SOURCES), GRID_COLS):
        row_sources = ALL_SOURCES[row_start : row_start + GRID_COLS]
        cols = st.columns(GRID_COLS)
        for idx, source in enumerate(row_sources):
            with cols[idx]:
                stats = _source_stats(campaigns, source)
                render_integration_card(source, stats, has_data=True)


def render_campaigns(campaigns: list[dict[str, Any]], source: str) -> None:
    """Kampagneside for én integration: tilbage, søgning, tabel."""
    # Header med tilbage-knap
    back_col, title_col = st.columns([1, 5], vertical_alignment="center")
    with back_col:
        if st.button("← Tilbage", use_container_width=True):
            _go_home()
            st.rerun()
    with title_col:
        st.title(source)
        st.caption("Kampagner for denne integration")

    # Kun kampagner for den valgte integration
    rows = [c for c in campaigns if c.get("source") == source]

    # Simpel søgning på kampagnenavn
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

    # List-of-dicts + st.table — ingen pandas/DataFrame, så Cloud's Arrow-dance
    # (pyarrow 26 segfault → force <25) ikke behøver at matche vores pins.
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


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="GTM overblik · Integrationer",
        page_icon="📊",
        layout="wide",
    )

    # Session-state til simpel navigation
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    if "selected_source" not in st.session_state:
        st.session_state["selected_source"] = None

    _inject_light_css()

    # Sidebar: kun minimal Dummy/Live-toggle (standard = Dummy)
    with st.sidebar:
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

    page = st.session_state.get("page", "home")
    selected = st.session_state.get("selected_source")

    if page == "campaigns" and selected in ALL_SOURCES:
        render_campaigns(campaigns, selected)
    else:
        # Sikrer at vi lander rent på forsiden hvis state er mærkelig
        st.session_state["page"] = "home"
        render_home(campaigns)


if __name__ == "__main__":
    main()
