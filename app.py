"""
GTM Campaign Overview — simpel Streamlit-app til Magnus.

Overblik først: to integrations-kort (Customer.io + Lemlist) med nøgletal.
Klik et kort → kampagnetabel for det værktøj. Tilbage via «← Overblik».

Happy path bruger Dummy data (ingen API-kald). Live API-klienterne nedenfor
er bevaret til senere — de kaldes kun hvis du aktivt vælger «Live APIs».

Kør lokalt:
  1. pip install -r requirements.txt
  2. cp .env.example .env   # kun nødvendigt til Live APIs
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
# Konstanter / fælles status-værdier (interne nøgler — APIs mapper hertil)
# ---------------------------------------------------------------------------
STATUS_ACTIVE = "active"
STATUS_PAUSE = "pause"
STATUS_DRAFT = "draft"
STATUS_FINISHED = "finished"

ALL_STATUSES = [STATUS_ACTIVE, STATUS_PAUSE, STATUS_DRAFT, STATUS_FINISHED]

# Danske labels til UI (filtre + tabel). Interne nøgler ovenfor ændres ikke.
STATUS_LABELS_DA = {
    STATUS_ACTIVE: "Aktiv",
    STATUS_PAUSE: "Pause",
    STATUS_DRAFT: "Draft",
    STATUS_FINISHED: "Afsluttet",
}
# Omvendt map: dansk label → intern nøgle (til filtre).
STATUS_FROM_DA = {v: k for k, v in STATUS_LABELS_DA.items()}

SOURCE_CUSTOMERIO = "Customer.io"
SOURCE_LEMLIST = "Lemlist"
ALL_SOURCES = [SOURCE_CUSTOMERIO, SOURCE_LEMLIST]

# Kolonner i den fælles tabel (én shape for begge værktøjer).
# Vi viser name, værktøj, status, leads, open/reply rate + et par rå tal.
TABLE_COLUMNS = [
    "name",
    "source",
    "status",
    "leads",
    "open_rate",
    "reply_rate",
    "sent",
    "replies",
]


# ---------------------------------------------------------------------------
# Hjælpere til metrics
# ---------------------------------------------------------------------------
def _safe_int(value: Any, default: int = 0) -> int:
    """Konverter til int uden at crashe på None / mærkelige typer."""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _rate_pct(numerator: int, denominator: int) -> float:
    """Procent: numerator/denominator*100 når denominator > 0, ellers 0."""
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 1)


def with_display_fields(campaign: dict[str, Any]) -> dict[str, Any]:
    """
    Tilføj felter til UI: dansk status + open_rate / reply_rate.

    Interne status-nøgler (active/pause/…) bevares i rå data til filtrering;
    her bygger vi en display-række til tabellen.
    """
    sent = _safe_int(campaign.get("sent"))
    opens = _safe_int(campaign.get("opens"))
    replies = _safe_int(campaign.get("replies"))
    leads = _safe_int(campaign.get("leads"))

    status_key = campaign.get("status", STATUS_DRAFT)
    return {
        "name": campaign.get("name", ""),
        "source": campaign.get("source", ""),
        "status": STATUS_LABELS_DA.get(status_key, str(status_key)),
        "leads": leads,
        "open_rate": _rate_pct(opens, sent),
        "reply_rate": _rate_pct(replies, sent),
        "sent": sent,
        "replies": replies,
    }


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
            "leads": 1400,
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
            "leads": 950,
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
            "leads": 320,
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
            "leads": 4800,
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
            "leads": 1100,
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
            "leads": 500,
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
            "leads": 180,
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
            "leads": 1650,
            "sent": 1500,
            "opens": 890,
            "clicks": 310,
            "replies": 95,
            "external_id": "lem_jkl012",
        },
    ]


# ---------------------------------------------------------------------------
# Status-mapping: API-værdier → vores fælles UI-status (interne nøgler)
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
        sent = _safe_int(
            item.get("sent")
            or metrics.get("sent")
            or metrics.get("delivered")
            or 0
        )
        opens = _safe_int(
            item.get("opens") or metrics.get("opened") or metrics.get("opens") or 0
        )
        clicks = _safe_int(
            item.get("clicks") or metrics.get("clicked") or metrics.get("clicks") or 0
        )
        # Customer.io har typisk ikke "leads" — brug sent som proxy for leads.
        leads = _safe_int(item.get("leads") or metrics.get("leads") or sent)

        normalized.append(
            {
                "name": item.get("name") or f"Campaign {item.get('id', '?')}",
                "source": SOURCE_CUSTOMERIO,
                "status": map_customerio_status(item),
                "leads": leads,
                "sent": sent,
                "opens": opens,
                "clicks": clicks,
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

        # nbLeads = antal leads i kampagnen (Lemlist-specifikt felt).
        leads = _safe_int(
            item.get("nbLeads")
            or item.get("leads")
            or stats.get("nbLeads")
            or metrics.get("leads")
            or 0
        )
        # sent = faktisk sendte mails (bruges til open_rate / reply_rate).
        sent_raw = item.get("sent")
        if sent_raw is None:
            sent_raw = stats.get("sent")
        if sent_raw is None:
            sent_raw = metrics.get("sent")
        # Hvis API ikke giver sent, brug leads som proxy (som tidligere version).
        sent = _safe_int(sent_raw if sent_raw is not None else leads)

        opens = _safe_int(
            item.get("opens")
            or stats.get("opened")
            or stats.get("opens")
            or metrics.get("opened")
            or 0
        )
        clicks = _safe_int(
            item.get("clicks")
            or stats.get("clicked")
            or stats.get("clicks")
            or metrics.get("clicked")
            or 0
        )
        replies = _safe_int(
            item.get("replied")
            or item.get("replies")
            or stats.get("replied")
            or stats.get("replies")
            or metrics.get("replied")
            or 0
        )

        normalized.append(
            {
                "name": item.get("name")
                or f"Campaign {item.get('_id') or item.get('id') or '?'}",
                "source": SOURCE_LEMLIST,
                "status": map_lemlist_status(item.get("status")),
                "leads": leads if leads > 0 else sent,
                "sent": sent,
                "opens": opens,
                "clicks": clicks,
                "replies": replies,
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
# Streamlit UI — overblik → detalje (session_state)
# ---------------------------------------------------------------------------
# Navigation: st.session_state["selected_source"]
#   None            → overblik (to integrations-kort)
#   "Customer.io"   → kampagnetabel for Customer.io
#   "Lemlist"       → kampagnetabel for Lemlist
#
# Streamlit har ikke ægte klikbare kort — vi bruger st.button under hvert kort.


def _init_session_state() -> None:
    """Sørg for at navigations-nøglen findes (None = overblik)."""
    if "selected_source" not in st.session_state:
        st.session_state.selected_source = None


def _campaigns_for_source(
    campaigns: list[dict[str, Any]], source: str
) -> list[dict[str, Any]]:
    """Filtrér kampagner til ét værktøj (source)."""
    return [c for c in campaigns if c.get("source") == source]


def _source_stats(
    campaigns: list[dict[str, Any]], source: str
) -> dict[str, int]:
    """
    Nøgletal til overblikskortet: total + aktive.

    Pause/draft/afsluttet tælles ikke på kortet — hold det scannbart.
    """
    subset = _campaigns_for_source(campaigns, source)
    return {
        "total": len(subset),
        "active": sum(1 for c in subset if c.get("status") == STATUS_ACTIVE),
    }


def _dataframe_column_config() -> dict[str, Any]:
    """Fælles danske kolonne-labels til st.dataframe."""
    return {
        "name": st.column_config.TextColumn("Navn"),
        "source": st.column_config.TextColumn("Værktøj"),
        "status": st.column_config.TextColumn("Status"),
        "leads": st.column_config.NumberColumn("Leads", format="%d"),
        "open_rate": st.column_config.NumberColumn("Open rate", format="%.1f%%"),
        "reply_rate": st.column_config.NumberColumn(
            "Reply rate", format="%.1f%%"
        ),
        "sent": st.column_config.NumberColumn("Sent", format="%d"),
        "replies": st.column_config.NumberColumn("Replies", format="%d"),
    }


def render_overview(campaigns: list[dict[str, Any]]) -> None:
    """
    Forside: to integrations-kort side om side.

    Hvert kort viser total + aktive. Knappen under kortet åbner detaljen.
    """
    st.subheader("Integrationer")
    st.caption("Vælg et værktøj for at se kampagnerne.")

    cols = st.columns(2)
    for col, source in zip(cols, ALL_SOURCES):
        stats = _source_stats(campaigns, source)
        with col:
            # Visuelt «kort»: container + metrics + knap (klik = åbn detalje).
            with st.container(border=True):
                st.markdown(f"### {source}")
                m1, m2 = st.columns(2)
                m1.metric("Kampagner i alt", stats["total"])
                m2.metric("Aktive", stats["active"])

                if st.button(
                    f"Åbn {source}",
                    key=f"open_{source}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state.selected_source = source
                    st.rerun()


def render_detail(
    campaigns: list[dict[str, Any]], source: str
) -> None:
    """
    Detaljevisning for ét værktøj: lille status-filter + kampagnetabel.

    Store filtre hører IKKE til forsiden — kun her, og kun status.
    """
    # Tilbage til overblik.
    if st.button("← Overblik", key="back_to_overview"):
        st.session_state.selected_source = None
        st.rerun()

    st.subheader(source)
    subset = _campaigns_for_source(campaigns, source)

    # Subtilt status-filter (kun på detaljesiden).
    status_options_da = [STATUS_LABELS_DA[s] for s in ALL_STATUSES]
    selected_statuses_da = st.multiselect(
        "Filtrér på status",
        options=status_options_da,
        default=status_options_da,
        help="Valgfrit — viser alle statusser som standard.",
    )
    selected_statuses = {STATUS_FROM_DA[label] for label in selected_statuses_da}

    filtered = [c for c in subset if c.get("status") in selected_statuses]

    st.caption(f"{len(filtered)} kampagne(r) vist")

    if not filtered:
        st.write("Ingen kampagner matcher filteret.")
        return

    display_rows = [with_display_fields(c) for c in filtered]
    st.dataframe(
        display_rows,
        use_container_width=True,
        hide_index=True,
        column_order=TABLE_COLUMNS,
        column_config=_dataframe_column_config(),
    )


def main() -> None:
    st.set_page_config(
        page_title="GTM Campaign Overview",
        page_icon="📊",
        layout="wide",
    )
    _init_session_state()

    st.title("GTM Campaign Overview")
    st.caption(
        "Overblik over Customer.io og Lemlist — start med integrationerne, "
        "klik dig ind på kampagnerne."
    )

    # --- Sidebar: kun datakilde (minimal). Ingen store filtre her. ---
    with st.sidebar:
        st.header("Indstillinger")
        # Default = Dummy data (index=0). Live APIs er valgfrit og uberørt
        # på happy path — klientkoden ovenfor kaldes kun i Live-mode.
        mode = st.radio(
            "Datakilde",
            options=["Dummy data", "Live APIs"],
            index=0,
            help=(
                "Dummy data kræver ingen API-nøgler (anbefalet til UI). "
                "Live APIs læser nøgler fra .env / miljøvariabler."
            ),
        )
        st.divider()
        st.markdown(
            "Tip: kopiér `.env.example` → `.env` og udfyld nøglerne "
            "før du skifter til **Live APIs**."
        )

    # --- Hent data (Dummy = happy path, ingen netværk) ---
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

    # --- Navigation: overblik ELLER detalje ---
    selected = st.session_state.selected_source
    if selected is None:
        render_overview(campaigns)
    elif selected in ALL_SOURCES:
        render_detail(campaigns, selected)
    else:
        # Ukendt værdi i session_state → reset til overblik.
        st.session_state.selected_source = None
        render_overview(campaigns)


if __name__ == "__main__":
    main()

