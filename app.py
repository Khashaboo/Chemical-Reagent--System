import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# Fix for internal network SSL
ssl._create_default_https_context = ssl._create_unverified_context

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="MARC Reagent OS", page_icon="🧪", layout="wide")

# Initialize Session State Memory (Simulates database writes for the demo)
if 'demo_saved_data' not in st.session_state:
    st.session_state.demo_saved_data = {}

# 2. CLEAN CSS INJECTION
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .logo-container { display: flex; align-items: center; margin-bottom: 2rem; }
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
    
    # Safely ensure critical columns exist
    critical_cols = ["Batch\\Lot Number", "Chemical Code", "Reagent Name", "Open Date", "EXP Date", "MSDS Link", "CoA Link"]
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

# ==========================================
# MODE 1: MOBILE SCANNER VIEW
# ==========================================
if batch_scanned:
    try:
        st.image("marc_logo.png", width=150)
    except:
        pass 
    
    reagent_row = df[df['Batch\\Lot Number'] == batch_scanned]
    
    if reagent_row.empty:
        st.error(f"❌ Batch '{batch_scanned}' not found in the database.")
    else:
        # Create a copy so we can apply our demo edits to it
        reagent = reagent_row.iloc[0].copy()
        
        # Override with demo data if the user has hit 'Save'
        if batch_scanned in st.session_state.demo_saved_data:
            override = st.session_state.demo_saved_data[batch_scanned]
            reagent['Chemical Code'] = override['code']
            reagent['Open Date'] = override['open_date']
            reagent['EXP Date'] = override['exp_date']
        
        current_open_date = safe_parse_date(reagent.get('Open Date', ''))
        current_exp_date = safe_parse_date(reagent.get('EXP Date', reagent.get('Exp Date', '')))
        
        current_code = str(reagent.get('Chemical Code', ''))
        if current_code == "nan": current_code = ""
        
        reagent_name = str(reagent.get('Reagent Name', 'Unknown Reagent'))
        if reagent_name == "nan": reagent_name = "Unknown Reagent"

        # Header Section
        st.subheader("🧪 Reagent Verification")
        st.title(reagent_name)
        
        # MAKE BATCH NUMBER HUGE AND CLEAR
        st.markdown(
            f"""
            <div style="background-color: #EEEEEE; padding: 15px; border-radius: 8px; border-left: 6px solid #E65100; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #333;">🏷️ Batch/Lot Number:</h3>
                <h1 style="margin: 0; color: #E65100; font-size: 2.5rem;">{batch_scanned}</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
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
                # Save to session state to simulate a database update
                st.session_state.demo_saved_data[batch_scanned] = {
                    'code': new_code,
                    'open_date': new_open_date,
                    'exp_date': new_exp_date
                }
                # Rerun the app instantly to show the updated Red/Green status
                st.rerun()

        st.divider()
        
        # Documentation Section
        st.markdown("#### 📑 Safety & Quality Documents")
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
# MODE 2: DESKTOP DASHBOARD
# ==========================================
else:
    col1, col2 = st.columns([1, 4])
    with col1:
        try:
            st.image("marc_logo.png", width=180)
        except:
            pass
    with col2:
        st.title("Bioequivalence Lab Reagents")
        st.write("Centralized inventory management and compliance dashboard.")
    
    st.divider()
    
    m1, m2, m3 = st.columns(3)
    total_reagents = len(df)
    m1.metric(label="Total Active Batches", value=total_reagents)
    m2.metric(label="Compliance Status", value="Ready for Audit")
    m3.metric(label="System Environment", value="Cloud Prototype")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    search = st.text_input("🔍 Search by Reagent Name or Batch Number...", placeholder="Type to filter...")
    
    display_df = df.copy()
    if search:
        display_df = display_df[display_df['Reagent Name'].str.contains(search, case=False, na=False) | 
                                display_df['Batch\\Lot Number'].str.contains(search, case=False, na=False)]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MSDS Link": st.column_config.LinkColumn("MSDS", display_text="Open Document"),
            "CoA Link": st.column_config.LinkColumn("CoA", display_text="Open Document"),
        }
    )