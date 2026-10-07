import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# Fix for internal network SSL
ssl._create_default_https_context = ssl._create_unverified_context

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="MARC Chemicals", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

# Initialize Session State Memory (Temporary for Prototype)
if 'demo_saved_data' not in st.session_state:
    st.session_state.demo_saved_data = {}

# 2. APP STYLING
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; font-family: 'Segoe UI', Roboto, sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div.row-widget.stRadio > div {
        background-color: #FFFFFF; border-radius: 12px; padding: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #E0E0E0;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E65100, #F44336); color: white; border: none; border-radius: 12px; padding: 0.75rem; font-weight: 700; font-size: 1.1rem; box-shadow: 0 4px 12px rgba(230,81,0,0.3); transition: all 0.3s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 16px rgba(230,81,0,0.4); transform: translateY(-1px);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. BULLETPROOF DATA LOADING
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQopdi6UaQgJKJLRVmblHEHX_691XJaPtk5E18SveGkWALreSCPUAw8uuC5rLNNCqNXSgVoDH7mc4PU/pub?output=csv"

@st.cache_data(ttl=10)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.dropna(how='all', inplace=True)
    
    # Force EXACT internal column names based on column position (Immune to Google Sheet header typos)
    if len(df.columns) >= 8:
        df.columns = [
            "Chemical Name", 
            "Batch_Number", 
            "Open Date", 
            "EXP Date After openning", 
            "Chemical Code", 
            "Opened By", 
            "MSDS Link", 
            "CoA Link"
        ] + list(df.columns[8:])
    
    df["Batch_Number"] = df["Batch_Number"].astype(str).str.strip()
    return df

df = load_data()

def safe_parse_date(date_val):
    try:
        return datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.now().date()

query_params = st.query_params
batch_scanned = query_params.get("batch")

team_members = [
    "Not Signed", "ElZahraa Mostafa", "Osama Gamal", "Mariam Sabry", "Marina Mamdouh", 
    "Marina Shafik", "Mohamed Ragab", "Youssef Ahmed", "Amr Hazem", "Omar Ahmed"
]

# ==========================================
# HEADER: LOGO & VIEW SWITCHER
# ==========================================
col_logo, col_spacer, col_toggle = st.columns([1, 1, 2])
with col_logo:
    try:
        st.image("marc_logo.png", width=140)
    except:
        st.markdown("<h3 style='margin:0; color:#1A1A1A;'>MARC</h3>", unsafe_allow_html=True)

with col_toggle:
    default_view = 0 if batch_scanned else 1
    view_mode = st.radio(
        "Display Mode", 
        ["📱 Mobile App View", "💻 Desktop Dashboard"], 
        horizontal=True, 
        index=default_view,
        label_visibility="collapsed"
    )

st.write("") 
st.divider()

# ==========================================
# MODE 1: NATIVE MOBILE APP VIEW
# ==========================================
if view_mode == "📱 Mobile App View":
    
    _, app_col, _ = st.columns([1, 2, 1])
    
    with app_col:
        if not batch_scanned:
            batch_scanned = st.selectbox("🔍 Select or search for a Batch Number:", df["Batch_Number"].tolist())
            
        if batch_scanned:
            reagent_row = df[df['Batch_Number'] == batch_scanned]
            
            if reagent_row.empty:
                st.error(f"❌ Batch '{batch_scanned}' not found.")
            else:
                reagent = reagent_row.iloc[0].copy()
                
                # Apply Demo Overrides
                if batch_scanned in st.session_state.demo_saved_data:
                    override = st.session_state.demo_saved_data[batch_scanned]
                    reagent['Chemical Name'] = override.get('Chemical Name', reagent.get('Chemical Name', ''))
                    reagent['Chemical Code'] = override.get('Chemical Code', reagent.get('Chemical Code', ''))
                    reagent['Open Date'] = override.get('Open Date', reagent.get('Open Date', ''))
                    reagent['EXP Date After openning'] = override.get('EXP Date After openning', reagent.get('EXP Date After openning', ''))
                    reagent['Opened By'] = override.get('Opened By', reagent.get('Opened By', ''))
                
                # Robust extraction
                chemical_name = str(reagent.get('Chemical Name', '')).strip()
                if not chemical_name or chemical_name.lower() == "nan":
                    chemical_name = "Unknown Chemical"
                    
                current_code = str(reagent.get('Chemical Code', ''))
                if current_code == "nan": current_code = ""
                
                current_open_date = safe_parse_date(reagent.get('Open Date', ''))
                current_exp_date = safe_parse_date(reagent.get('EXP Date After openning', ''))
                
                current_opened_by = str(reagent.get('Opened By', 'Not Signed')).strip()
                if current_opened_by == "nan" or current_opened_by == "": current_opened_by = "Not Signed"
                opened_by_index = team_members.index(current_opened_by) if current_opened_by in team_members else 0

                days_left = (current_exp_date - datetime.now().date()).days
                abs_days_left = abs(days_left)
                days_label = "Remaining" if days_left >= 0 else "Ago"
                
                if days_left < 0:
                    status_color, status_icon, status_text, banner_gradient = "#F44336", "🚨", "EXPIRED", "linear-gradient(135deg, #D32F2F, #B71C1C)"
                elif days_left <= 7:
                    status_color, status_icon, status_text, banner_gradient = "#FF9800", "⚠️", "WARNING", "linear-gradient(135deg, #F57C00, #E65100)"
                else:
                    status_color, status_icon, status_text, banner_gradient = "#4CAF50", "✅", "VALID", "linear-gradient(135deg, #43A047, #2E7D32)"

                # --- NATIVE APP UI: TITLE (HARDCODED INLINE CSS) ---
                st.markdown(f"<h4 style='text-align: center; color: #7D7D7D; font-size: 1rem; text-transform: uppercase; margin-bottom: -10px;'>🧪 Reagent Verification</h4>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='text-align: center; color: #1A1A1A; font-size: 2.5rem; font-weight: 900; margin-bottom: 25px;'>{chemical_name}</h1>", unsafe_allow_html=True)
                
                # --- NATIVE APP UI: CARDS ---
                st.markdown(
                    f"""
                    <div style="background: {banner_gradient}; border-radius: 16px; padding: 20px; color: white; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
                        <div>
                            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; font-weight: 600;">Batch / Lot Number</div>
                            <div style="font-size: 26px; font-weight: 900; letter-spacing: 1px; margin-top: 5px;">{batch_scanned}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 50%; width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; font-size: 22px;">🏷️</div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 15px; margin-bottom: 25px;">
                        <div style="flex: 1; background: white; border-radius: 16px; padding: 15px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #EBEBEB;">
                            <div style="font-size: 28px; margin-bottom: 5px; color: {status_color};">{status_icon}</div>
                            <div style="font-size: 13px; font-weight: 800; color: #333; letter-spacing: 0.5px;">{status_text}</div>
                        </div>
                        <div style="flex: 1; background: white; border-radius: 16px; padding: 15px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #EBEBEB;">
                            <div style="font-size: 24px; font-weight: 900; color: {status_color}; margin-bottom: 2px;">{abs_days_left}</div>
                            <div style="font-size: 11px; font-weight: 700; color: #888; letter-spacing: 0.5px; text-transform: uppercase;">Days {days_label}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                # --- NATIVE APP UI: EDIT FORM ---
                st.markdown("#### 📝 Edit Details")
                with st.form("edit_reagent_form", border=True):
                    new_opened_by = st.selectbox("Opened by:", team_members, index=opened_by_index)
                    new_code = st.text_input("Chemical Code", value=current_code, placeholder="e.g., CHM-001")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        new_open_date = st.date_input("Open Date", value=current_open_date)
                    with c2:
                        new_exp_date = st.date_input("Exp Date After openning", value=current_exp_date)
                        
                    submitted = st.form_submit_button("💾 Save & Sign", type="primary", use_container_width=True)
                    if submitted:
                        st.session_state.demo_saved_data[batch_scanned] = {
                            'Chemical Name': chemical_name,
                            'Chemical Code': new_code,
                            'Open Date': str(new_open_date),
                            'EXP Date After openning': str(new_exp_date),
                            'Opened By': new_opened_by
                        }
                        st.rerun()

                st.write("") 
                
                # --- NATIVE APP UI: DOCUMENTS ---
                st.markdown("#### 📑 Safety Documents")
                d1, d2 = st.columns(2)
                msds_val = str(reagent.get('MSDS Link', ''))
                coa_val = str(reagent.get('CoA Link', ''))
                
                with d1:
                    if msds_val and msds_val.lower() != "nan":
                        st.link_button("📄 View MSDS", msds_val, use_container_width=True)
                    else:
                        st.button("📄 MSDS Not Available", disabled=True, use_container_width=True)
                with d2:
                    if coa_val and coa_val.lower() != "nan":
                        st.link_button("🔬 View CoA", coa_val, use_container_width=True)
                    else:
                        st.button("🔬 CoA Not Available", disabled=True, use_container_width=True)

# ==========================================
# MODE 2: DESKTOP DASHBOARD VIEW
# ==========================================
else:
    st.title("Bioequivalence Lab Reagents")
    st.write("Centralized inventory management and compliance dashboard.")
    
    m1, m2, m3 = st.columns(3)
    total_reagents = len(df)
    m1.metric(label="Total Active Batches", value=total_reagents)
    m2.metric(label="Compliance Status", value="Ready for Audit")
    m3.metric(label="System Environment", value="Cloud Prototype")
    
    st.write("")
    search = st.text_input("🔍 Search by Chemical Name or Batch Number...", placeholder="Type to filter...")
    
    display_df = df.copy()
    if search:
        display_df = display_df[display_df['Chemical Name'].str.contains(search, case=False, na=False) | 
                                display_df['Batch_Number'].str.contains(search, case=False, na=False)]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MSDS Link": st.column_config.LinkColumn("MSDS", display_text="Open Document"),
            "CoA Link": st.column_config.LinkColumn("CoA", display_text="Open Document"),
        }
    )