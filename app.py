import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# --- FIX FOR CORPORATE NETWORK SSL ERRORS ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION & BRANDING ---
st.set_page_config(page_title="MARC Reagent OS", page_icon="🧪", layout="centered")
st.image("marc_logo.png", width=300)

# Injecting MARC Brand Identity (Red, Orange, Yellow, Black)
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background-color: #FAFAFA;
    }
    
    /* Custom Headers matching MARC Black */
    h1, h2, h3 {
        color: #1E1E1E !important;
        font-family: 'Arial', sans-serif;
    }
    
    /* Style the Primary 'Save' Button with MARC Red/Orange */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #D32F2F 0%, #F57C00 100%);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #B71C1C 0%, #E65100 100%);
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }

    /* Style the Link Buttons (MSDS / CoA) */
    .stLinkButton > a {
        border: 2px solid #FBC02D !important;
        color: #1E1E1E !important;
        border-radius: 8px;
        font-weight: bold;
    }
    .stLinkButton > a:hover {
        background-color: #FBC02D !important;
        color: black !important;
    }
    
    /* Hide Streamlit Default Menu & Footer for Professional Look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Your live published CSV link
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQopdi6UaQgJKJLRVmblHEHX_691XJaPtk5E18SveGkWALreSCPUAw8uuC5rLNNCqNXSgVoDH7mc4PU/pub?output=csv"

@st.cache_data(ttl=60) # Refreshes faster for prototype testing
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.columns = df.columns.str.strip()
    df["Batch\\Lot Number"] = df["Batch\\Lot Number"].astype(str).str.strip()
    # Ensure Chemical Code column exists to prevent errors if not added to sheet yet
    if "Chemical Code" not in df.columns:
        df["Chemical Code"] = ""
    return df

df = load_data()

# --- ROUTING LOGIC ---
query_params = st.query_params
batch_scanned = query_params.get("batch")

# --- Helper to parse dates safely ---
def safe_parse_date(date_val):
    try:
        return datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.now().date()

# ==========================================
# MODE 1: MOBILE SCANNER VIEW (QR Scanned)
# ==========================================
if batch_scanned:
    reagent_row = df[df['Batch\\Lot Number'] == batch_scanned]
    
    if reagent_row.empty:
        st.error(f"❌ Batch '{batch_scanned}' not found in the MARC database.")
    else:
        reagent = reagent_row.iloc[0]
        
        # Parse Dates for the Editable Inputs
        current_open_date = safe_parse_date(reagent['Open Date'])
        current_exp_date = safe_parse_date(reagent['EXP Date'])
        current_code = str(reagent.get('Chemical Code', ''))
        if current_code == "nan": current_code = ""

        # --- HEADER ---
        st.markdown("### 🔬 MARC Bioequivalence Lab")
        st.title(reagent['Reagent Name'])
        st.caption(f"**Batch/Lot Number:** {batch_scanned}")
        
        # Expiry Status Calculation (Poka-Yoke)
        days_left = (current_exp_date - datetime.now().date()).days
        if days_left < 0:
            st.error(f"🚨 **STATUS: EXPIRED** ({abs(days_left)} days ago). Do not use.")
        elif days_left <= 7:
            st.warning(f"⚠️ **STATUS: EXPIRING SOON** ({days_left} days remaining).")
        else:
            st.success(f"✅ **STATUS: PASSED**. Valid for {days_left} days.")
            
        st.markdown("---")
        
        # --- EDITABLE DATA FORM ---
        st.markdown("#### 📝 Edit Reagent Data")
        with st.form("edit_reagent_form"):
            new_code = st.text_input("Chemical Code", value=current_code, placeholder="e.g., CHM-001")
            
            col1, col2 = st.columns(2)
            with col1:
                new_open_date = st.date_input("Open Date", value=current_open_date)
            with col2:
                new_exp_date = st.date_input("Exp Date (After Opening)", value=current_exp_date)
                
            submitted = st.form_submit_button("💾 Save Updates to Database")
            
            if submitted:
                # Placeholder for Phase 3 Database Write capabilities
                st.info("🔄 UI is ready! To write these changes back to the Google Sheet, we need to set up IT Service Account API credentials.")

        st.markdown("---")
        
        # --- DOCUMENTATION LINKS ---
        st.markdown("#### 📑 Safety & Quality Documents")
        doc1, doc2 = st.columns(2)
        with doc1:
            if pd.notna(reagent['MSDS Link']) and str(reagent['MSDS Link']).strip() != "":
                st.link_button("📄 View MSDS", str(reagent['MSDS Link']), use_container_width=True)
            else:
                st.button("📄 MSDS Not Available", disabled=True, use_container_width=True)
        with doc2:
            if pd.notna(reagent['CoA Link']) and str(reagent['CoA Link']).strip() != "":
                st.link_button("🔬 View CoA", str(reagent['CoA Link']), use_container_width=True)
            else:
                st.button("🔬 CoA Not Available", disabled=True, use_container_width=True)

# ==========================================
# MODE 2: MANAGER DASHBOARD (Desktop View)
# ==========================================
else:
    st.markdown("### 🔬 MARC Bioequivalence Lab")
    st.title("🧪 Reagent Inventory Dashboard")
    st.write("Overview of all active reagents. Scan a QR code to view and edit specific batches.")
    
    search = st.text_input("🔍 Search by Reagent Name or Batch...")
    if search:
        df = df[df['Reagent Name'].str.contains(search, case=False, na=False) | 
                df['Batch\\Lot Number'].str.contains(search, case=False, na=False)]
        
    st.dataframe(df, use_container_width=True, hide_index=True)