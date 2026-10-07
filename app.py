import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# Fix for internal network SSL
ssl._create_default_https_context = ssl._create_unverified_context

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="MARC Reagent OS", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

# Initialize Session State Memory
if 'demo_saved_data' not in st.session_state:
    st.session_state.demo_saved_data = {}

# 2. ENTERPRISE CSS & APP STYLING
st.markdown("""
<style>
    /* App background */
    .stApp { background-color: #F8F9FA; font-family: 'Segoe UI', Roboto, sans-serif; }
    
    /* Clean up the Top Header padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    /* Segmented Control / Radio Button Styling for the View Switcher */
    div.row-widget.stRadio > div {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
    }
    
    /* Primary Save Button */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E65100, #F44336);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(230,81,0,0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 16px rgba(230,81,0,0.4);
        transform: translateY(-1px);
    }
    
    /* Hide Streamlit Watermarks */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. DATA LOADING
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQopdi6UaQgJKJLRVmblHEHX_691XJaPtk5E18SveGkWALreSCPUAw8uuC5rLNNCqNXSgVoDH7mc4PU/pub?output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Updated to match the exact column names from your new Google Sheet structure
    critical_cols = ["Batch\\Lot Number", "Chemical Code", "Reagent Name", "Open Date", "EXP Date After openning", "Signature", "MSDS Link", "CoA Link"]
    for col in critical_cols:
        if col not in df.columns:
            df[col] = ""
            
    df["Batch\\Lot Number"] = df["Batch\\Lot Number"].astype(str).str.strip()
    return df

df = load_data()

def safe_parse_date(date_val):
    try:
        return datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.now().date()

query_params = st.query_params
batch_scanned = query_params.get("batch")

# Team Signatures List
signatures_list = [
    "Not Signed", 
    "ElZahraa Mostafa", 
    "Osama Gamal", 
    "Mariam Sabry", 
    "Marina Mamdouh", 
    "Marina Shafik", 
    "Mohamed Ragab", 
    "Youssef Ahmed", 
    "Amr Hazem", 
    "Omar Ahmed"
]

# ==========================================
# HEADER: LOGO (TOP LEFT) & VIEW SWITCHER
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
            batch_scanned = st.selectbox("🔍 Select or search for a Batch Number:", df["Batch\\Lot Number"].tolist())
            
        if batch_scanned:
            reagent_row = df[df['Batch\\Lot Number'] == batch_scanned]
            
            if reagent_row.empty:
                st.error(f"❌ Batch '{batch_scanned}' not found.")
            else:
                reagent = reagent_row.iloc[0].copy()
                
                # Load temporary edits if saved in demo mode
                if batch_scanned in st.session_state.demo_saved_data:
                    override = st.session_state.demo_saved_data[batch_scanned]
                    reagent['Chemical Code'] = override['code']
                    reagent['Open Date'] = override['open_date']
                    reagent['EXP Date After openning'] = override['exp_date']
                    reagent['Signature'] = override['signature']
                
                # Safely parse updated column names
                current_open_date = safe_parse_date(reagent.get('Open Date', ''))
                current_exp_date = safe_parse_date(reagent.get('EXP Date After openning', reagent.get('EXP Date', '')))
                
                current_code = str(reagent.get('Chemical Code', ''))
                if current_code == "nan": current_code = ""
                
                reagent_name = str(reagent.get('Reagent Name', 'Unknown Reagent'))
                if reagent_name == "nan": reagent_name = "Unknown Reagent"
                
                current_sig = str(reagent.get('Signature', 'Not Signed')).strip()
                if current_sig == "nan" or current_sig == "": current_sig = "Not Signed"
                sig_index = signatures_list.index(current_sig) if current_sig in signatures_list else 0

                days_left = (current_exp_date - datetime.now().date()).days
                
                if days_left < 0:
                    status_color, status_icon, status_text = "#F44336", "🚨", "EXPIRED"
                    banner_gradient = "linear-gradient(135deg, #D32F2F, #B71C1C)"
                elif days_left <= 7:
                    status_color, status_icon, status_text = "#FF9800", "⚠️", "WARNING"
                    banner_gradient = "linear-gradient(135deg, #F57C00, #E65100)"
                else:
                    status_color, status_icon, status_text = "#4CAF50", "✅", "VALID"
                    banner_gradient = "linear-gradient(135deg, #43A047, #2E7D32)"

                # --- NATIVE APP UI: HERO SECTION ---
                st.markdown(f"<h2 style='text-align: center; margin-bottom: 20px; color: #1E1E1E; font-weight: 800;'>{reagent_name}</h2>", unsafe_allow_html=True)
                
                st.markdown(
                    f"""
                    <div style="background: {banner_gradient}; border-radius: 16px; padding: 20px; color: white; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
                        <div>
                            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; font-weight: 600;">Batch / Lot Number</div>
                            <div style="font-size: 26px; font-weight: 900; letter-spacing: 1px; margin-top: 5px;">{batch_scanned}</div>
                        </div>
                        <div style="background: rgba(255,255,255,