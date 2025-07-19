import os
import re
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from colorama import init, Fore, Style
import pyfiglet
from urllib.parse import urlparse, urljoin
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv
import time

# Load .env file
load_dotenv()

init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("wan_scraps.log"),
        logging.StreamHandler()
    ]
)

def banner():
    ascii_banner = pyfiglet.figlet_format("Wan Scraps", font="slant")
    print(Fore.MAGENTA + ascii_banner + Style.RESET_ALL)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    logging.error("Discord webhook URL not set in .env. Please set DISCORD_WEBHOOK_URL.")
    exit(1)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc != ''

def escape_markdown(text: str) -> str:
    escape_chars = r'\*_`~|>'
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

def safe_truncate(text: str, max_len=700) -> str:
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text

def fetch_website_content(url: str):
    try:
        start = time.time()
        response = session.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        load_time = time.time() - start
        logging.info(f"[✓] Fetched {url} (Status: {response.status_code}, Load Time: {load_time:.2f}s)")
        return response.text, response.status_code, response.headers, load_time
    except requests.RequestException as e:
        status_code = getattr(e.response, 'status_code', 'N/A')
        logging.error(f"[✗] Failed to fetch {url} (Status: {status_code}) - {e}")
        return None, status_code, {}, 0

def extract_json_ld(soup):
    data = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(script.string)
            data.append(d)
        except Exception:
            continue
    return data if data else ["Not found"]

def extract_open_graph(soup):
    og = {}
    for tag in soup.find_all("meta"):
        prop = tag.get("property") or tag.get("name") or ""
        if prop.startswith("og:") or prop.startswith("twitter:"):
            og[prop] = tag.get("content", "Not found")
    return og if og else {"None": "Not found"}

def find_favicons(soup, base_url):
    icons = []
    for link in soup.find_all("link", rel=lambda x: x and "icon" in x.lower()):
        href = link.get("href")
        if href:
            icons.append(urljoin(base_url, href))
    return icons if icons else ["Not found"]

def get_main_images(soup, base_url, max_images=5):
    images = []
    for img in soup.find_all("img", src=True):
        src = img.get("src")
        if src:
            images.append(urljoin(base_url, src))
        if len(images) >= max_images:
            break
    return images if images else ["Not found"]

def get_canonical_url(soup, base_url):
    link = soup.find("link", rel="canonical")
    if link and link.get("href"):
        return urljoin(base_url, link.get("href"))
    return "Not found"

def get_robots_meta(soup):
    tag = soup.find("meta", attrs={"name": "robots"})
    if tag and tag.get("content"):
        return tag.get("content").strip()
    return "Not found"

def count_links(soup, base_url):
    internal = set()
    external = set()
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc.lower()
    for a in soup.find_all("a", href=True):
        href = a.get("href").strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        domain = parsed_url.netloc.lower()
        if domain == base_domain:
            internal.add(full_url)
        else:
            external.add(full_url)
    return list(internal), list(external)

def smart_scrape(html: str, base_url: str, response_headers: dict, load_time: float) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    title = soup.title.string.strip() if soup.title and soup.title.string else "Title not found"

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else "Meta description not found"

    meta_keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    meta_keywords = meta_keywords_tag.get("content", "").strip() if meta_keywords_tag else "Meta keywords not found"

    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all("h1") if h1.get_text(strip=True)]
    headlines = h1_tags[:5] or ["No H1 tags found"]

    h2_tags = [h2.get_text(strip=True) for h2 in soup.find_all("h2") if h2.get_text(strip=True)]
    subheadlines = h2_tags[:5] or ["No H2 tags found"]

    paragraphs = [
        p.get_text(strip=True) for p in soup.find_all("p")
        if p.get_text(strip=True) and len(p.get_text(strip=True)) > 50
    ]
    summaries = paragraphs[:5] or ["No meaningful paragraphs found"]

    charset = None
    charset_tag = soup.find("meta", charset=True)
    if charset_tag:
        charset = charset_tag.get("charset", None)
    else:
        content_type = soup.find("meta", attrs={"http-equiv": "Content-Type"})
        if content_type and "charset=" in content_type.get("content", ""):
            charset = content_type.get("content").split("charset=")[-1]

    lang = soup.html.attrs.get("lang") if soup.html else None

    json_ld = extract_json_ld(soup)
    og_tags = extract_open_graph(soup)
    favicons = find_favicons(soup, base_url)
    main_images = get_main_images(soup, base_url)
    canonical_url = get_canonical_url(soup, base_url)
    robots_meta = get_robots_meta(soup)
    internal_links, external_links = count_links(soup, base_url)

    last_modified = response_headers.get("Last-Modified", "Not found")
    content_length = response_headers.get("Content-Length", "Unknown")
    server = response_headers.get("Server", "Unknown")

    return {
        "title": title,
        "meta_description": meta_desc,
        "meta_keywords": meta_keywords,
        "headlines": headlines,
        "subheadlines": subheadlines,
        "summaries": summaries,
        "charset": charset or "Unknown",
        "lang": lang or "Unknown",
        "json_ld": json_ld,
        "open_graph": og_tags,
        "favicons": favicons,
        "main_images": main_images,
        "canonical_url": canonical_url,
        "robots_meta": robots_meta,
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "internal_links_sample": internal_links[:5] or ["None"],
        "external_links_sample": external_links[:5] or ["None"],
        "last_modified": last_modified,
        "content_length": content_length,
        "server": server,
        "load_time": load_time,
    }

def format_json_ld(json_ld_data):
    try:
        if isinstance(json_ld_data, list):
            pretty = "\n".join(json.dumps(item, indent=2) if isinstance(item, dict) else str(item) for item in json_ld_data[:2])
        else:
            pretty = json.dumps(json_ld_data, indent=2)
        return safe_truncate(pretty, 700)
    except Exception:
        return "Error formatting JSON-LD"

def send_discord_embed(webhook_url, domain, scraped_data, url, status_code):
    status_text = f"{status_code} OK" if status_code == 200 else f"Error: {status_code}"
    color = 0x2ecc71 if status_code == 200 else 0xe74c3c

    fields = [
        {"name": "Status", "value": status_text, "inline": True},
        {"name": "Load Time (s)", "value": f"{scraped_data['load_time']:.2f}", "inline": True},
        {"name": "Server", "value": scraped_data['server'], "inline": True},
        {"name": "Content Length (bytes)", "value": scraped_data['content_length'], "inline": True},
        {"name": "Last-Modified", "value": scraped_data['last_modified'], "inline": False},

        {"name": "Title", "value": safe_truncate(escape_markdown(scraped_data['title'])), "inline": False},
        {"name": "Meta Description", "value": safe_truncate(escape_markdown(scraped_data['meta_description'])), "inline": False},
        {"name": "Meta Keywords", "value": safe_truncate(escape_markdown(scraped_data['meta_keywords'])), "inline": False},

        {"name": "Charset", "value": scraped_data['charset'], "inline": True},
        {"name": "Language", "value": scraped_data['lang'], "inline": True},
        {"name": "Canonical URL", "value": scraped_data['canonical_url'], "inline": False},

        {"name": "Robots Meta", "value": scraped_data['robots_meta'], "inline": False},

        {"name": f"Top {len(scraped_data['headlines'])} H1 Headlines", 
         "value": safe_truncate("\n".join(f"- {escape_markdown(h)}" for h in scraped_data['headlines'])), "inline": False},

        {"name": f"Top {len(scraped_data['subheadlines'])} H2 Subheadlines", 
         "value": safe_truncate("\n".join(f"- {escape_markdown(h)}" for h in scraped_data['subheadlines'])), "inline": False},

        {"name": f"Summary Paragraphs", 
         "value": safe_truncate("\n".join(f"- {escape_markdown(s)}" for s in scraped_data['summaries'])), "inline": False},

        {"name": f"Favicons ({len(scraped_data['favicons'])})", 
         "value": safe_truncate("\n".join(scraped_data['favicons']), 700), "inline": False},

        {"name": f"Main Images ({len(scraped_data['main_images'])})", 
         "value": safe_truncate("\n".join(scraped_data['main_images']), 700), "inline": False},

        {"name": f"Open Graph & Twitter Cards", 
         "value": safe_truncate("\n".join(f"{escape_markdown(k)}: {escape_markdown(v)}" for k, v in scraped_data['open_graph'].items()), 700), "inline": False},

        {"name": f"Internal Links Count", "value": str(scraped_data['internal_links_count']), "inline": True},
        {"name": "Internal Links Sample", "value": safe_truncate("\n".join(scraped_data['internal_links_sample']), 700), "inline": False},

        {"name": f"External Links Count", "value": str(scraped_data['external_links_count']), "inline": True},
        {"name": "External Links Sample", "value": safe_truncate("\n".join(scraped_data['external_links_sample']), 700), "inline": False},

        {"name": f"JSON-LD Structured Data (first 2 blocks)", "value": format_json_ld(scraped_data['json_ld']), "inline": False},
    ]

    embed = {
        "title": f"Wan Scraps: {domain}",
        "url": url,
        "color": color,
        "fields": fields,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": f"Checked by Wan Scraps • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        }
    }

    payload = {
        "username": "Wan Scraps Bot",
        "avatar_url": "https://www.python.org/static/favicon.ico",
        "embeds": [embed]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"[✔] Sent embed to Discord for {domain} ({status_text})")
    except requests.RequestException as e:
        logging.error(f"[✘] Failed to send webhook for {domain}: {e}")

def get_urls_from_input():
    print(Fore.YELLOW + "Enter website URLs to scrape (separate multiple URLs with commas):")
    user_input = input().strip()
    urls = [url.strip() for url in user_input.split(",") if url.strip()]
    return urls

def main():
    banner()

    import sys
    if len(sys.argv) > 1:
        urls = sys.argv[1:]
    else:
        urls = get_urls_from_input()

    if not urls:
        print(Fore.RED + "No URLs provided. Exiting.")
        return

    for url in urls:
        if not is_valid_url(url):
            logging.warning(f"Invalid URL skipped: {url}")
            print(Fore.RED + f"Invalid URL skipped: {url}")
            continue

        logging.info(f"Starting scrape for: {url}")
        print(Fore.CYAN + f"[...] Scraping: {url}")

        html, status_code, response_headers, load_time = fetch_website_content(url)

        if not html:
            scraped_data = {
                "title": "N/A",
                "meta_description": "N/A",
                "meta_keywords": "N/A",
                "headlines": ["Failed to retrieve content."],
                "subheadlines": ["Failed to retrieve content."],
                "summaries": ["Failed to retrieve content."],
                "charset": "N/A",
                "lang": "N/A",
                "json_ld": ["N/A"],
                "open_graph": {"N/A": "N/A"},
                "favicons": ["N/A"],
                "main_images": ["N/A"],
                "canonical_url": "N/A",
                "robots_meta": "N/A",
                "internal_links_count": 0,
                "external_links_count": 0,
                "internal_links_sample": [],
                "external_links_sample": [],
                "last_modified": "N/A",
                "content_length": "N/A",
                "server": "N/A",
                "load_time": 0,
            }
        else:
            scraped_data = smart_scrape(html, url, response_headers, load_time)

        domain = urlparse(url).netloc
        send_discord_embed(DISCORD_WEBHOOK_URL, domain, scraped_data, url, status_code)

if __name__ == "__main__":
    main()
