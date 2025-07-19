# 🕸️ Wan Scraps

Wan Scraps is a Python CLI tool that scrapes web pages for metadata, OpenGraph, JSON-LD, canonical links, favicons, images, headers, and more, and sends a structured embed report to a Discord channel via webhook.

## ✨ Features

- Structured metadata scraping (title, meta tags, H1/H2, etc.)
- JSON-LD and OpenGraph detection
- Favicon and image collection
- Link statistics (internal/external)
- Sends all info as a Discord embed

## 🧰 Requirements

- Python 3.8+
- A Discord webhook URL

## 📦 Installation

```bash
git clone https://github.com/your-username/wan-scraps.git
cd wan-scraps
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
