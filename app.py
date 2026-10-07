import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# Fix for internal network SSL
ssl._create_default_https_context = ssl._create_unverified_context

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="MARC Reagent OS", page_icon="🧪", layout="centered")

# Initialize Session State Memory
if 'demo_saved_data' not in st.session_state:
    st.session_state.demo_saved_data = {}

# 2. MOBILE-FIRST ENTERPRISE CSS
st.markdown("""
<style>
    /* App background */
    .stApp { background-color: #F4F6F8; }
    
    /* Align Logo Image to the Top Left */
    [data-testid="stImage"] {
        display: flex;
        justify-content: flex-start;
        margin-bottom: -10px;
    }
    
    /* Centered Mobile Typography */
    .header-sub {
        text-align: center;
        color: #7D7D7D;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 5px;
        margin-top: 20px;
    }
    .header-title {
        text-align: center;
        color: #1A1A1A;
        font-size: 2.2rem !important;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 25px;
    }
    
    /* Native App Card Style for Batch Number */
    .batch-card {
        background-color: #FFFFFF;
        padding: 25px 15px;
        border-radius: 16px;
        border-top: 6px solid #E65100;
        box-shadow: 0 8px 16px rgba(0,0,0,0.06);
        text-align: center;
        margin-bottom: 25px;
    }
    .batch-label {
        margin: 0;
        color: #8E8E8E;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .batch-value {
        margin: 10px 0 0 0;
        color: #E65100;
        font-size: 2.4rem;
        font-weight: 900;
        letter-spacing: 1.5px;
    }

    /* Primary Button Styling */
    div.stButton > button[kind="primary"] {
        background-color: #E65100;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 10px rgba(230,81,0,0.2);
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #BF360C;
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
        st.image("marc_logo.png", width=120)
    except:
        pass 
    
    reagent_row = df[df['Batch\\Lot Number'] == batch_scanned]
    
    if reagent_row.empty:
        st.error(f"❌ Batch '{batch_scanned}' not found in the database.")
    else:
        reagent = reagent_row.iloc[0].copy()
        
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

        # Centered Headers
        st.markdown(f"<p class='header-sub'>🧪 Reagent Verification</p>", unsafe_allow_html=True)
        st.markdown(f"<h1 class='header-title'>{reagent_name}</h1>", unsafe_allow_html=True)
        
        # Native Mobile Card for Batch Number
        st.markdown(
            f"""
            <div class="batch-card">
                <p class="batch-label">🏷️ Batch / Lot Number</p>
                <h1 class="batch-value">{batch_scanned}</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Status Alert
        days_left = (current_exp_date - datetime.now().date()).days
        if days_left < 0:
            st.error(f"🚨 **EXPIRED** • {abs(days_left)} days ago • DO NOT USE", icon="🚫")
        elif days_left <= 7:
            st.warning(f"⚠️ **EXPIRING SOON** • {days_left} days remaining", icon="⚠️")
        else:
            st.success(f"✅ **VALID** • {days_left} days remaining", icon="✅")
            
        st.write("") # Spacer
        
        # Form
        st.markdown("#### 📝 Edit Details")
        with st.form("edit_reagent_form", border=True):
            new_code = st.text_input("Chemical Code", value=current_code, placeholder="e.g., CHM-001")
            
            # Streamlit automatically stacks columns on small screens
            c1, c2 = st.columns(2)
            with c1:
                new_open_date = st.date_input("Open Date", value=current_open_date)
            with c2:
                new_exp_date = st.date_input("Exp Date", value=current_exp_date)
                
            submitted = st.form_submit_button("💾 Save Updates", type="primary", use_container_width=True)
            if submitted:
                st.session_state.demo_saved_data[batch_scanned] = {
                    'code': new_code,
                    'open_date': str(new_open_date),
                    'exp_date': str(new_exp_date)
                }
                st.rerun()

        st.write("") # Spacer
        
        # Documents
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
    
    st.write("")
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