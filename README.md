# Wan Scraps

**Wan Scraps** is a powerful Python tool for scraping structured metadata, SEO tags, images, Open Graph data, JSON-LD, and link information from web pages — then reporting the results to a **Discord webhook** in a clean, structured embed.

Ideal for SEO analysis, website audits, and metadata inspection via Discord.

---

## 🔧 Features

- **Metadata Extraction**
  - `<title>`, `<meta name="description">`, `<meta name="keywords">`
  - Canonical URL (`<link rel="canonical">`)
  - Charset (`<meta charset>` or content-type)
  - HTML `lang` attribute
  - `robots` meta tag

- **Content Parsing**
  - Extracts top `<h1>` and `<h2>` headings
  - Collects paragraph summaries with character length filtering
  - Supports structured summaries of site content

- **Structured Data & Social Metadata**
  - Parses `application/ld+json` blocks (JSON-LD structured data)
  - Extracts Open Graph & Twitter Card metadata (`og:*`, `twitter:*`)

- **Visual Content**
  - Finds favicons (`<link rel="icon">`, etc.)
  - Extracts key images from `<img>` tags (with base URL resolution)

- **Link Analytics**
  - Detects internal and external links
  - Counts and samples both types

- **Request Handling**
  - Uses `requests` session with retry logic
  - Tracks load time and request status
  - Logs server headers (`Server`, `Last-Modified`, `Content-Length`)

- **Discord Reporting**
  - Sends all scraped data as a structured Discord embed
  - Automatically escapes markdown to prevent Discord formatting issues
  - Truncates long fields to avoid message cutoffs

---

## 📦 Requirements

- Python 3.8+
- A valid [Discord Webhook URL](https://discord.com/developers/docs/resources/webhook)

---

## 🚀 Installation

```bash
git clone https://github.com/your-username/wan-scraps.git
cd wan-scraps
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
