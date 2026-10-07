import html
import os
import re
import ssl
import urllib.error
import urllib.request
from datetime import date, datetime
from io import StringIO

import pandas as pd
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="MARC Reagent OS",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "demo_saved_data" not in st.session_state:
    st.session_state.demo_saved_data = {}

# ==========================================
# 2. CONSTANTS
# ==========================================
SHEET_ID = "1mfteEKngJV58MxbozXLO_t3ChxI8WsCLinWFMtqpAyo"  # Reagent_Inventory_Master
SHEET_CSV_URLS = [
    u for u in [
        os.environ.get("SHEET_CSV_URL", "").strip(),  # optional override (env var / Streamlit secret)
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0",
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQopdi6UaQgJKJLRVmblHEHX_691XJaPtk5E18SveGkWALreSCPUAw8uuC5rLNNCqNXSgVoDH7mc4PU/pub?output=csv",
    ] if u
]

# Internal names, assigned strictly by column position in the sheet
COLUMNS = [
    "Chemical Name", "Batch_Number", "Open Date", "EXP Date After openning",
    "Chemical Code", "Opened By", "MSDS Link", "CoA Link",
]
COL_NAME, COL_BATCH, COL_OPEN, COL_EXP, COL_CODE, COL_BY, COL_MSDS, COL_COA = COLUMNS

BUILD_ID = "2026-10-07-v3"  # bump when you redeploy; shown under the header
WARNING_DAYS = 7
NOT_SIGNED = "Not Signed"
TEAM_MEMBERS = [
    NOT_SIGNED, "ElZahraa Mostafa", "Osama Gamal", "Mariam Sabry", "Marina Mamdouh",
    "Marina Shafik", "Mohamed Ragab", "Youssef Ahmed", "Amr Hazem", "Omar Ahmed",
]
DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]

# ==========================================
# 3. STYLING
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; font-family: 'Segoe UI', Roboto, sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div.row-widget.stRadio > div {
        background-color: #FFFFFF; border-radius: 12px; padding: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #E0E0E0;
    }
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E65100, #F44336); color: white; border: none;
        border-radius: 12px; padding: 0.75rem; font-weight: 700; font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(230,81,0,0.3); transition: all 0.3s ease;
    }
    div.stButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 16px rgba(230,81,0,0.4); transform: translateY(-1px);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. HELPERS
# ==========================================
def render_html(markup: str) -> None:
    """Render HTML cards without Markdown ever touching them.

    Markdown turns lines indented 4+ spaces into code blocks, which is what
    printed the raw <div> tags. We strip indentation AND use st.html (which
    skips the Markdown parser) when the Streamlit version has it.
    """
    flat = "".join(line.strip() for line in markup.splitlines())
    if hasattr(st, "html"):
        st.html(flat)
    else:
        st.markdown(flat, unsafe_allow_html=True)


def esc(value) -> str:
    """Escape sheet values before putting them in HTML (names may contain & or <)."""
    return html.escape(str(value), quote=True)


def today() -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Africa/Cairo")).date()
    except Exception:
        return date.today()


def parse_date(value):
    """Return a date, or None when empty/unparseable (never silently 'today')."""
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def clean(value) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.lower() == "nan" else text


def get_status(exp_date):
    """-> (days_left, color, icon, text, gradient)"""
    if exp_date is None:
        return None, "#757575", "❓", "NO EXPIRY DATE", "linear-gradient(135deg, #757575, #424242)"
    days_left = (exp_date - today()).days
    if days_left < 0:
        return days_left, "#F44336", "🚨", "EXPIRED", "linear-gradient(135deg, #D32F2F, #B71C1C)"
    if days_left <= WARNING_DAYS:
        return days_left, "#FF9800", "⚠️", "WARNING", "linear-gradient(135deg, #F57C00, #E65100)"
    return days_left, "#4CAF50", "✅", "VALID", "linear-gradient(135deg, #43A047, #2E7D32)"


def _download_csv(url: str) -> str:
    """Download with normal SSL verification first; fall back to unverified
    only for this one request if the internal network breaks certificates
    (instead of disabling verification for the entire process)."""
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.read().decode("utf-8-sig")
    except urllib.error.URLError as err:
        if isinstance(err.reason, ssl.SSLError):
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(url, timeout=20, context=ctx) as resp:
                return resp.read().decode("utf-8-sig")
        raise


ALIASES = {
    "chemicalname": COL_NAME,
    "batchnumber": COL_BATCH, "batchlotnumber": COL_BATCH, "lotnumber": COL_BATCH, "batch": COL_BATCH,
    "opendate": COL_OPEN,
    "expdateafteropenning": COL_EXP, "expdateafteropening": COL_EXP, "expdate": COL_EXP,
    "chemicalcode": COL_CODE,
    "openedby": COL_BY,
    "msdslink": COL_MSDS, "coalink": COL_COA,
}


def _norm(header) -> str:
    return re.sub(r"[^a-z0-9]", "", str(header).lower())


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Match sheet headers by name (so 'Batch\\Lot Number' works); if the names
    can't all be matched, fall back to column position."""
    by_name = {}
    for col in df.columns:
        key = ALIASES.get(_norm(col))
        if key and key not in by_name.values():
            by_name[col] = key
    if set(by_name.values()) == set(COLUMNS):
        return df.rename(columns=by_name)
    positional = {df.columns[i]: COLUMNS[i] for i in range(min(len(df.columns), len(COLUMNS)))}
    return df.rename(columns=positional)


def _fetch_first_working() -> str:
    errors = []
    for url in SHEET_CSV_URLS:
        try:
            raw = _download_csv(url)
            # Google returns a sign-in HTML page (HTTP 200) when a sheet isn't shared
            if raw.lstrip()[:15].lower().startswith(("<!doctype html", "<html")):
                raise ValueError("sheet is not shared publicly (got a sign-in page)")
            return raw
        except Exception as exc:  # try the next source
            errors.append(f"{url[:60]}...: {exc}")
    raise RuntimeError(" | ".join(errors))


@st.cache_data(ttl=30, show_spinner=False)
def load_data() -> pd.DataFrame:
    raw = _fetch_first_working()
    # dtype=str keeps batch numbers exactly as typed (no 1267 -> 1267.0, no lost zeros)
    df = pd.read_csv(StringIO(raw), dtype=str).dropna(how="all")
    df = map_columns(df)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS].fillna("")
    for col in COLUMNS:
        df[col] = df[col].astype(str).str.strip()

    # Rows without a batch number can never be scanned/selected
    df = df[df[COL_BATCH] != ""]
    return df.reset_index(drop=True)


def apply_overrides(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for batch, values in st.session_state.demo_saved_data.items():
        mask = out[COL_BATCH] == batch
        for col, val in values.items():
            out.loc[mask, col] = val
    return out


def add_status_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    days, labels = [], []
    for raw in out[COL_EXP]:
        d, _, icon, text, _ = get_status(parse_date(raw))
        days.append(d)
        labels.append(f"{icon} {text.title()}")
    out["Days Left"] = pd.array(days, dtype="Int64")
    out["Status"] = labels
    return out


# ==========================================
# 5. LOAD DATA
# ==========================================
try:
    df = apply_overrides(load_data())
except Exception as exc:
    st.error("❌ Could not load the reagent sheet. Check the network / sheet link and try again.")
    st.caption(f"Details: {exc}")
    st.stop()

batch_param = st.query_params.get("batch", "")
if isinstance(batch_param, list):
    batch_param = batch_param[0] if batch_param else ""
batch_param = clean(batch_param)

# ==========================================
# 6. HEADER: LOGO & VIEW SWITCHER
# ==========================================
col_logo, _, col_toggle = st.columns([1, 1, 2])
with col_logo:
    if os.path.exists("marc_logo.png"):
        st.image("marc_logo.png", width=140)
    else:
        st.markdown("<h3 style='margin:0; color:#1A1A1A;'>MARC</h3>", unsafe_allow_html=True)

with col_toggle:
    view_mode = st.radio(
        "Display Mode",
        ["📱 Mobile App View", "💻 Desktop Dashboard"],
        horizontal=True,
        index=0 if batch_param else 1,
        label_visibility="collapsed",
    )

st.write("")
st.divider()
st.caption(f"Build: {BUILD_ID}")

# ==========================================
# MODE 1: MOBILE APP VIEW
# ==========================================
if view_mode == "📱 Mobile App View":
    _, app_col, _ = st.columns([1, 2, 1])

    with app_col:
        batch_list = df[COL_BATCH].tolist()

        # Pre-select the QR-scanned batch (case-insensitive); never default to a random batch
        default_idx = None
        if batch_param:
            matches = [i for i, b in enumerate(batch_list) if b.lower() == batch_param.lower()]
            if matches:
                default_idx = matches[0]
            else:
                st.warning(f"Batch '{batch_param}' from the QR code was not found. Please search below.")

        selected_batch = st.selectbox(
            "🔍 Select or search for a Batch Number:",
            batch_list,
            index=default_idx,
            placeholder="Type to search...",
            key="batch_select",
        )

        if selected_batch:
            rows = df[df[COL_BATCH] == selected_batch]
            if len(rows) > 1:
                st.warning(f"⚠️ Batch '{selected_batch}' appears {len(rows)} times in the sheet. Showing the first one.")
            reagent = rows.iloc[0]

            chemical_name = clean(reagent[COL_NAME]) or "Unknown Chemical"
            current_code = clean(reagent[COL_CODE])
            open_date = parse_date(reagent[COL_OPEN])
            exp_date = parse_date(reagent[COL_EXP])

            opened_by = clean(reagent[COL_BY]) or NOT_SIGNED
            opened_by_index = TEAM_MEMBERS.index(opened_by) if opened_by in TEAM_MEMBERS else 0

            days_left, status_color, status_icon, status_text, banner_gradient = get_status(exp_date)
            if days_left is None:
                days_value, days_label = "—", "No Date"
            else:
                days_value = abs(days_left)
                days_label = "Days Remaining" if days_left >= 0 else "Days Ago"

            # --- Master card (indented for readability; render_html flattens it) ---
            render_html(f"""
                <div style="background:{banner_gradient}; border-radius:16px; padding:25px; color:white;
                            margin-bottom:20px; box-shadow:0 4px 15px rgba(0,0,0,0.15);">
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                border-bottom:1px solid rgba(255,255,255,0.25); padding-bottom:15px; margin-bottom:15px;">
                        <div>
                            <div style="font-size:11px; text-transform:uppercase; letter-spacing:1.5px; opacity:0.9; font-weight:700;">Chemical Name</div>
                            <div style="font-size:24px; font-weight:900; letter-spacing:0.5px; margin-top:4px; line-height:1.2;">{esc(chemical_name)}</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.2); border-radius:50%; min-width:45px; height:45px;
                                    display:flex; justify-content:center; align-items:center; font-size:22px;">🧪</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:11px; text-transform:uppercase; letter-spacing:1.5px; opacity:0.9; font-weight:700;">Batch / Lot Number</div>
                            <div style="font-size:22px; font-weight:900; letter-spacing:1px; margin-top:4px;">{esc(selected_batch)}</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.2); border-radius:50%; min-width:45px; height:45px;
                                    display:flex; justify-content:center; align-items:center; font-size:22px;">🏷️</div>
                    </div>
                </div>
            """)

            # --- Status cards ---
            render_html(f"""
                <div style="display:flex; gap:15px; margin-bottom:25px;">
                    <div style="flex:1; background:white; border-radius:16px; padding:15px; text-align:center;
                                box-shadow:0 2px 8px rgba(0,0,0,0.04); border:1px solid #EBEBEB;">
                        <div style="font-size:28px; margin-bottom:5px; color:{status_color};">{status_icon}</div>
                        <div style="font-size:13px; font-weight:800; color:#333; letter-spacing:0.5px;">{status_text}</div>
                    </div>
                    <div style="flex:1; background:white; border-radius:16px; padding:15px; text-align:center;
                                box-shadow:0 2px 8px rgba(0,0,0,0.04); border:1px solid #EBEBEB;">
                        <div style="font-size:24px; font-weight:900; color:{status_color}; margin-bottom:2px;">{days_value}</div>
                        <div style="font-size:11px; font-weight:700; color:#888; letter-spacing:0.5px; text-transform:uppercase;">{days_label}</div>
                    </div>
                </div>
            """)

            # --- Edit form ---
            st.markdown("#### 📝 Edit Details")
            with st.form(f"edit_form_{selected_batch}", border=True):
                new_opened_by = st.selectbox("Opened by:", TEAM_MEMBERS, index=opened_by_index)
                new_code = st.text_input("Chemical Code", value=current_code, placeholder="e.g., CHM-001")

                c1, c2 = st.columns(2)
                with c1:
                    new_open_date = st.date_input("Open Date", value=open_date or today())
                with c2:
                    new_exp_date = st.date_input("Exp Date After Opening", value=exp_date or today())

                submitted = st.form_submit_button("💾 Save & Sign", type="primary", use_container_width=True)
                if submitted:
                    if new_opened_by == NOT_SIGNED:
                        st.error("Please select who opened the reagent before signing.")
                    elif new_exp_date < new_open_date:
                        st.error("Expiry date cannot be earlier than the open date.")
                    else:
                        st.session_state.demo_saved_data[selected_batch] = {
                            COL_CODE: new_code.strip(),
                            COL_OPEN: new_open_date.isoformat(),
                            COL_EXP: new_exp_date.isoformat(),
                            COL_BY: new_opened_by,
                        }
                        st.rerun()

            st.write("")

            # --- Safety documents ---
            st.markdown("#### 📑 Safety Documents")
            d1, d2 = st.columns(2)
            msds_val = clean(reagent[COL_MSDS])
            coa_val = clean(reagent[COL_COA])

            with d1:
                if msds_val.lower().startswith("http"):
                    st.link_button("📄 View MSDS", msds_val, use_container_width=True)
                else:
                    st.button("📄 MSDS Not Available", disabled=True, use_container_width=True)
            with d2:
                if coa_val.lower().startswith("http"):
                    st.link_button("🔬 View CoA", coa_val, use_container_width=True)
                else:
                    st.button("🔬 CoA Not Available", disabled=True, use_container_width=True)

# ==========================================
# MODE 2: DESKTOP DASHBOARD
# ==========================================
else:
    st.title("Bioequivalence Lab Reagents")
    st.write("Centralized inventory management and compliance dashboard.")

    full_df = add_status_columns(df)
    expired = int((full_df["Days Left"] < 0).sum())
    expiring = int(full_df["Days Left"].between(0, WARNING_DAYS).sum())
    unsigned = int((full_df[COL_BY].replace("", NOT_SIGNED) == NOT_SIGNED).sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Active Batches", len(full_df))
    m2.metric("Expired", expired)
    m3.metric(f"Expiring ≤ {WARNING_DAYS} days", expiring)
    m4.metric("Not Signed", unsigned)

    st.write("")
    search = st.text_input("🔍 Search by Chemical Name or Batch Number...", placeholder="Type to filter...")

    display_df = full_df
    if search:
        mask = (
            display_df[COL_NAME].str.contains(search, case=False, na=False, regex=False)
            | display_df[COL_BATCH].str.contains(search, case=False, na=False, regex=False)
        )
        display_df = display_df[mask]

    display_df = display_df.rename(columns={COL_EXP: "Exp Date After Opening"})

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MSDS Link": st.column_config.LinkColumn("MSDS", display_text="Open Document"),
            "CoA Link": st.column_config.LinkColumn("CoA", display_text="Open Document"),
        },
    )
