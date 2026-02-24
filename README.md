# Cloud VM Price Tracker (Paris)

Daily updated dashboard comparing VM prices for Scaleway, AWS, and OVHcloud in the Paris region.

## 🚀 Features
- **Daily Updates:** Automation via GitHub Actions (00:00 UTC+7).
- **3 Providers:** Scaleway (fr-par-1), AWS (eu-west-3), OVHcloud (GRA/SBG).
- **Dashboard:** Interactive HTML with search, sort, and filters (ARM/GPU/x86).

## 🛠 Tech Stack
- **Data Retrieval:** Python (`scripts/fetch_prices.py`)
- **Dashboard Builder:** Python (`scripts/build_dashboard.py`)
- **CI/CD:** GitHub Actions (`.github/workflows/daily.yml`)
- **Frontend:** Vanilla JS/CSS (`index.html`)

## 📖 Setup
1. Enable **GitHub Pages** (Settings -> Pages -> Source: **GitHub Actions**).
2. Everything handles itself once pushed to `main`.
