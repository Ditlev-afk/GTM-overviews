"""
GTM Campaign Overview — simpel Streamlit-app til Magnus.

Henter kampagner fra Customer.io (App API) og Lemlist, normaliserer dem
til én tabel, og lader dig filtrere på status + værktøj.

Kør lokalt:
  1. pip install -r requirements.txt
  2. cp .env.example .env   # udfyld nøgler hvis du vil bruge Live APIs
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

ALL_STATUSES = [STATUS_ACTIVE, STATUS_PAUSE, STATUS_DRAFT, STATUS_FINISHED]
SOURCE_CUSTOMERIO = "Customer.io"
SOURCE_LEMLIST = "Lemlist"
ALL_SOURCES = [SOURCE_CUSTOMERIO, SOURCE_LEMLIST]

# Kolonner i den fælles tabel (én shape for begge værktøjer).
TABLE_COLUMNS = [
    "name",
    "source",
    "status",
    "sent",
    "opens",
    "clicks",
    "replies",
    "external_id",
]


# ---------------------------------------------------------------------------
# Dummy-data — bruges når du tester UI uden API-nøgler
# ---------------------------------------------------------------------------
def get_dummy_campaigns() -> list[dict[str, Any]]:
    """Returnerer et lille, realistisk dummy-datasæt fra begge værktøjer."""
    return [
        {
            "name": "Onboarding drip — nye trials",
            "source": SOURCE_CUSTOMERIO,
            "status": STATUS_ACTIVE,
            "sent": 1240,
            "opens": 610,
            "clicks": 188,
            "replies": 42,
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
            "external_id": "cio-088",
        },
        {
            "name": "Outbound — Nordic SaaS founders",
            "source": SOURCE_LEMLIST,
            "status": STATUS_ACTIVE,
            "sent": 980,
            "opens": 520,
            "clicks": 145,
            "replies": 67,
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
            "external_id": "lem_jkl012",
        },
    ]


# ---------------------------------------------------------------------------
# Status-mapping: API-værdier → vores fælles UI-status
# ---------------------------------------------------------------------------
def map_customerio_status(campaign: dict[str, Any]) -> str:
    """Map Customer.io `active` / `state` til vores status-værdier."""
    # Dokumenteret felt: active (bool) + state (str). State-værdier kan variere.
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

    # Fallback hvis state mangler: brug active-flaget.
    if active is True:
        return STATUS_ACTIVE
    if active is False:
        return STATUS_PAUSE
    return STATUS_DRAFT


def map_lemlist_status(raw_status: Any) -> str:
    """Map Lemlist-status (running/paused/draft/ended/…) til vores UI-status."""
    # Lemlist kan returnere en streng ELLER en liste af statusser.
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


# ---------------------------------------------------------------------------
# Thin API-klienter
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

    # Svaret er typisk {"campaigns": [...]} — men vi håndterer også en ren liste.
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

        # Metrics ligger ofte på et separat endpoint (/metrics).
        # Vi tager simple felter hvis de findes på listen; ellers 0.
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

        normalized.append(
            {
                "name": item.get("name") or f"Campaign {item.get('id', '?')}",
                "source": SOURCE_CUSTOMERIO,
                "status": map_customerio_status(item),
                "sent": _safe_int(sent),
                "opens": _safe_int(opens),
                "clicks": _safe_int(clicks),
                # Customer.io har typisk ikke "replies" på email-kampagner.
                "replies": _safe_int(item.get("replies") or metrics.get("replied")),
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
        # Basic auth: username="", password=api_key  →  header "Basic <base64(:key)>"
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

    # v2 kan returnere {"campaigns": [...]} eller en ren liste.
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

        # Lemlist-metrics: feltnavne kan variere (stats / metrics / top-level).
        stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}

        sent = (
            item.get("nbLeads")
            or item.get("sent")
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

        normalized.append(
            {
                "name": item.get("name") or f"Campaign {item.get('_id') or item.get('id') or '?'}",
                "source": SOURCE_LEMLIST,
                "status": map_lemlist_status(item.get("status")),
                "sent": _safe_int(sent),
                "opens": _safe_int(opens),
                "clicks": _safe_int(clicks),
                "replies": _safe_int(replies),
                "external_id": str(item.get("_id") or item.get("id") or ""),
            }
        )

    return normalized


def load_live_campaigns() -> list[dict[str, Any]]:
    """Hent fra begge API'er og slå resultaterne sammen (fejl stopper ikke resten)."""
    campaigns: list[dict[str, Any]] = []
    campaigns.extend(fetch_customerio_campaigns())
    campaigns.extend(fetch_lemlist_campaigns())
    return campaigns


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="GTM Campaign Overview",
        page_icon="📊",
        layout="wide",
    )

    st.title("GTM Campaign Overview")
    st.caption(
        "Samlet overblik over kampagner fra Customer.io og Lemlist "
        "(status + nøgletal)."
    )

    # --- Sidebar: data-mode + filtre ---
    with st.sidebar:
        st.header("Indstillinger")

        # Toggle: Dummy vs Live — så UI kan testes uden nøgler.
        mode = st.radio(
            "Datakilde",
            options=["Dummy data", "Live APIs"],
            index=0,
            help=(
                "Dummy data kræver ingen API-nøgler. "
                "Live APIs læser nøgler fra .env / miljøvariabler."
            ),
        )

        st.divider()
        st.subheader("Filtre")

        selected_statuses = st.multiselect(
            "Status",
            options=ALL_STATUSES,
            default=ALL_STATUSES,
        )
        selected_sources = st.multiselect(
            "Værktøj / source",
            options=ALL_SOURCES,
            default=ALL_SOURCES,
        )

        st.divider()
        st.markdown(
            "Tip: kopiér `.env.example` → `.env` og udfyld nøglerne "
            "før du skifter til **Live APIs**."
        )

    # --- Hent data ---
    if mode == "Dummy data":
        campaigns = get_dummy_campaigns()
        st.info("Viser dummy-data (ingen API-kald).")
    else:
        with st.spinner("Henter kampagner fra Customer.io og Lemlist…"):
            campaigns = load_live_campaigns()
        if not campaigns:
            st.warning(
                "Ingen kampagner hentet. Tjek API-nøgler, netværk og fejlbeskeder ovenfor. "
                "Skift til Dummy data for at teste UI'et."
            )

    # --- Filtrér ---
    filtered = [
        c
        for c in campaigns
        if c.get("status") in selected_statuses and c.get("source") in selected_sources
    ]

    # --- Vis tabel ---
    st.subheader(f"Kampagner ({len(filtered)})")

    if not filtered:
        st.write("Ingen kampagner matcher de valgte filtre.")
        return

    # st.dataframe viser en interaktiv tabel; vi beholder kolonne-rækkefølgen.
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_order=TABLE_COLUMNS,
        column_config={
            "name": st.column_config.TextColumn("Navn"),
            "source": st.column_config.TextColumn("Værktøj"),
            "status": st.column_config.TextColumn("Status"),
            "sent": st.column_config.NumberColumn("Sent"),
            "opens": st.column_config.NumberColumn("Opens"),
            "clicks": st.column_config.NumberColumn("Clicks"),
            "replies": st.column_config.NumberColumn("Replies"),
            "external_id": st.column_config.TextColumn("External ID"),
        },
    )


if __name__ == "__main__":
    main()
