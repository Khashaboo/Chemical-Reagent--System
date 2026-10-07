import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# Fix for internal network SSL
ssl._create_default_https_context = ssl._create_unverified_context

# 1. PAGE CONFIGURATION (Wide layout for professional look)
st.set_page_config(page_title="MARC Reagents", page_icon="🧪", layout="wide")

# 2. CLEAN CSS INJECTION
st.markdown("""
<style>
    /* Clean up the main background and text */
    .stApp { background-color: #F8F9FA; }
    
    /* Make the logo alignment cleaner */
    .logo-container { display: flex; align-items: center; margin-bottom: 2rem; }
    
    /* Style the Save button with MARC colors */
    div.stButton > button[kind="primary"] {
        background-color: #E65100;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #BF360C;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. DATA LOADING
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQopdi6UaQgJKJLRVmblHEHX_691XJaPtk5E18SveGkWALreSCPUAw8uuC5rLNNCqNXSgVoDH7mc4PU/pub?output=csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.columns = df.columns.str.strip()
    df["Batch\\Lot Number"] = df["Batch\\Lot Number"].astype(str).str.strip()
    if "Chemical Code" not in df.columns:
        df["Chemical Code"] = ""
    return df

df = load_data()

def safe_parse_date(date_val):
    try:
        return datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.now().date()

query_params = st.query_params
batch_scanned = query_params.get("batch")

# ==========================================
# MODE 1: MOBILE SCANNER VIEW (QR Triggered)
# ==========================================
if batch_scanned:
    st.image("marc_logo.png", width=150) # Smaller, aligned logo
    
    reagent_row = df[df['Batch\\Lot Number'] == batch_scanned]
    
    if reagent_row.empty:
        st.error(f"❌ Batch '{batch_scanned}' not found in the database.")
    else:
        reagent = reagent_row.iloc[0]
        
        current_open_date = safe_parse_date(reagent['Open Date'])
        current_exp_date = safe_parse_date(reagent['EXP Date'])
        current_code = str(reagent.get('Chemical Code', ''))
        if current_code == "nan": current_code = ""

        # Header Section
        st.subheader("🧪 Reagent Verification")
        st.title(reagent['Reagent Name'])
        st.caption(f"**Batch/Lot:** {batch_scanned}")
        
        # Status Card (Poka-Yoke)
        days_left = (current_exp_date - datetime.now().date()).days
        if days_left < 0:
            st.error(f"🚨 **EXPIRED** • {abs(days_left)} days ago • DO NOT USE", icon="🚫")
        elif days_left <= 7:
            st.warning(f"⚠️ **EXPIRING SOON** • {days_left} days remaining", icon="⚠️")
        else:
            st.success(f"✅ **VALID** • {days_left} days remaining", icon="✅")
            
        st.divider()
        
        # Editable Form Section
        st.markdown("#### 📝 Update Reagent Details")
        with st.form("edit_reagent_form", border=True):
            new_code = st.text_input("Chemical Code (Editable)", value=current_code, placeholder="e.g., CHM-001")
            
            c1, c2 = st.columns(2)
            with c1:
                new_open_date = st.date_input("Open Date", value=current_open_date)
            with c2:
                new_exp_date = st.date_input("Exp Date (After Opening)", value=current_exp_date)
                
            submitted = st.form_submit_button("💾 Save Updates", type="primary", use_container_width=True)
            if submitted:
                st.info("System is in Prototype Mode. Google Service Account API required to write data back.")

        st.divider()
        
        # Documentation Section
        st.markdown("#### 📑 Safety & Quality Documents")
        d1, d2 = st.columns(2)
        with d1:
            if pd.notna(reagent['MSDS Link']) and str(reagent['MSDS Link']).strip() != "":
                st.link_button("📄 View MSDS", str(reagent['MSDS Link']), use_container_width=True)
            else:
                st.button("📄 MSDS Not Available", disabled=True, use_container_width=True)
        with d2:
            if pd.notna(reagent['CoA Link']) and str(reagent['CoA Link']).strip() != "":
                st.link_button("🔬 View CoA", str(reagent['CoA Link']), use_container_width=True)
            else:
                st.button("🔬 CoA Not Available", disabled=True, use_container_width=True)

# ==========================================
# MODE 2: DESKTOP DASHBOARD (Default View)
# ==========================================
else:
    # Header Row
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("marc_logo.png", width=180)
    with col2:
        st.title("Bioequivalence Lab Reagents")
        st.write("Centralized inventory management and compliance dashboard.")
    
    st.divider()
    
    # Metrics Row
    m1, m2, m3 = st.columns(3)
    total_reagents = len(df)
    m1.metric(label="Total Active Batches", value=total_reagents)
    m2.metric(label="Compliance Status", value="Ready for Audit")
    m3.metric(label="System Environment", value="Cloud Prototype")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Search and Table
    search = st.text_input("🔍 Search by Reagent Name or Batch Number...", placeholder="Type to filter...")
    
    display_df = df.copy()
    if search:
        display_df = display_df[display_df['Reagent Name'].str.contains(search, case=False, na=False) | 
                                display_df['Batch\\Lot Number'].str.contains(search, case=False, na=False)]
    
    # Format the dataframe to look professional
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MSDS Link": st.column_config.LinkColumn("MSDS", display_text="Open Document"),
            "CoA Link": st.column_config.LinkColumn("CoA", display_text="Open Document"),
        }
    )