# 🧪 BE Chemical Reagent Operating System

A Lean Six Sigma (LSS) visual control dashboard for tracking laboratory reagent expiration dates and accessing safety documentation via mobile QR codes.

## 🎯 Project Goals
* **Poka-Yoke (Mistake-Proofing):** Eliminate the use of expired chemicals via automated Red/Green visual status indicators.
* **Zero Waste:** Instantly retrieve Material Safety Data Sheets (MSDS) and Certificates of Analysis (CoA) without leaving the lab bench.
* **GLP Compliance:** Maintain a strict, centralized database of all open and active reagents.

## ⚙️ How It Works
1. A unique QR code is generated for each reagent batch.
2. An analyst scans the QR code at the bench using a mobile device.
3. The Streamlit dashboard instantly displays the validity status, days remaining, and direct links to the approved PDF documentation.

## 🛠️ Technology Stack
* **Frontend:** Python (Streamlit)
* **Backend:** Cloud Database / CSV Pipeline
* **Deployment:** Designed for On-Premise Internal Hosting (Nginx / Reverse Proxy) for maximum data security.
