import streamlit as st
import pandas as pd
from datetime import datetime
import ssl

# --- ADD THESE TWO LINES TO FIX THE SSL ERROR ---
ssl._create_default_https_context = ssl._create_unverified_context
# ------------------------------------------------

# --- CONFIGURATION ---
st.set_page_config(page_title="Reagent OS", layout="centered")

# Your live published CSV link from Google Sheets
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQopdi6UaQgJKJLRVmblHEHX_691XJaPtk5E18SveGkWALreSCPUAw8uuC5rLNNCqNXSgVoDH7mc4PU/pub?output=csv"

@st.cache_data(ttl=300) # Refreshes data every 5 minutes
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    
    # Clean the column names by stripping accidental spaces
    df.columns = df.columns.str.strip()
    
    # Ensure Batch\Lot Number is a string to prevent scanning errors
    # Note: We use \\ in Python to represent a single \ in the sheet header
    df["Batch\\Lot Number"] = df["Batch\\Lot Number"].astype(str).str.strip()
    return df

df = load_data()

# --- ROUTING LOGIC ---
query_params = st.query_params
batch_scanned = query_params.get("batch")

# --- MODE 1: MOBILE SCANNER VIEW (If QR code is scanned) ---
if batch_scanned:
    reagent_row = df[df['Batch\\Lot Number'] == batch_scanned]
    
    if reagent_row.empty:
        st.error(f"❌ Batch {batch_scanned} not found in inventory.")
    else:
        reagent = reagent_row.iloc[0]
        
        # Calculate Expiry Status
        try:
            exp_date = datetime.strptime(str(reagent['EXP Date']).strip(), "%Y-%m-%d").date()
            days_left = (exp_date - datetime.now().date()).days
        except ValueError:
            # Fallback if date is missing or formatted incorrectly in the sheet
            exp_date = reagent['EXP Date']
            days_left = None 
            
        st.title(reagent['Reagent Name'])
        st.caption(f"Batch/Lot: {batch_scanned}")
        
        # Visual Control (Poka-Yoke)
        if days_left is not None:
            if days_left < 0:
                st.error(f"🚨 EXPIRED {abs(days_left)} days ago. Do not use.")
            elif days_left <= 7:
                st.warning(f"⚠️ EXPIRING SOON: {days_left} days remaining.")
            else:
                st.success(f"✅ PASSED. Valid for {days_left} days.")
        else:
            st.warning("⚠️ Expiry date format unknown. Please check the master sheet.")
            
        col1, col2 = st.columns(2)
        col1.metric("Opened On", str(reagent['Open Date']))
        col2.metric("Expires On", str(exp_date))
        
        st.markdown("---")
        if pd.notna(reagent['MSDS Link']) and str(reagent['MSDS Link']).strip() != "":
            st.link_button("📄 View MSDS", str(reagent['MSDS Link']), use_container_width=True)
        if pd.notna(reagent['CoA Link']) and str(reagent['CoA Link']).strip() != "":
            st.link_button("🔬 View CoA", str(reagent['CoA Link']), use_container_width=True)

# --- MODE 2: MANAGER DASHBOARD (If opened without a QR scan) ---
else:
    st.title("🧪 Lab Reagent Inventory Dashboard")
    st.write("Overview of all active reagents.")
    
    # Simple search bar
    search = st.text_input("Search by Reagent Name or Batch...")
    if search:
        df = df[df['Reagent Name'].str.contains(search, case=False, na=False) | 
                df['Batch\\Lot Number'].str.contains(search, case=False, na=False)]
        
    st.dataframe(df, use_container_width=True, hide_index=True)