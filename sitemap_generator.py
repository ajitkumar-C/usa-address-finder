import json
import os
from datetime import datetime

SITE_URL = "https://usa-address-zip.vercel.app/"
INDEX_JSON_PATH = "data/search-index.json"
SITEMAP_FILE = "sitemap.xml"

print("Generating sitemap.xml...")

if not os.path.exists(INDEX_JSON_PATH):
    print(f"Error: {INDEX_JSON_PATH} not found. Run build_site.py first.")
    exit(1)

with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

current_date = datetime.now().strftime("%Y-%m-%d")

urls = []

# 1. Homepage
urls.append({
    "loc": SITE_URL,
    "lastmod": current_date,
    "changefreq": "weekly",
    "priority": "1.0"
})
urls.append({
    "loc": f"{SITE_URL}index.html",
    "lastmod": current_date,
    "changefreq": "weekly",
    "priority": "0.9"
})

# 1b. Distance Calculator Page
urls.append({
    "loc": f"{SITE_URL}distance.html",
    "lastmod": current_date,
    "changefreq": "weekly",
    "priority": "0.8"
})

# 1c. Random Address Generator Page
urls.append({
    "loc": f"{SITE_URL}address-generator.html",
    "lastmod": current_date,
    "changefreq": "weekly",
    "priority": "0.8"
})

# 1c. Info Pages
for info in ["about.html", "contact.html", "privacy.html", "disclaimer.html"]:
    urls.append({
        "loc": f"{SITE_URL}{info}",
        "lastmod": current_date,
        "changefreq": "monthly",
        "priority": "0.5"
    })

# 2. State pages
for state in data["states"]:
    urls.append({
        "loc": f"{SITE_URL}state/{state['s']}.html",
        "lastmod": current_date,
        "changefreq": "weekly",
        "priority": "0.8"
    })

# 3. County pages
for county in data["counties"]:
    urls.append({
        "loc": f"{SITE_URL}county/{county['s']}.html",
        "lastmod": current_date,
        "changefreq": "monthly",
        "priority": "0.6"
    })

# Write XML content
print(f"Adding {len(urls)} URLs to sitemap...")

xml_content = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

for url in urls:
    xml_content.append("  <url>")
    xml_content.append(f"    <loc>{url['loc']}</loc>")
    xml_content.append(f"    <lastmod>{url['lastmod']}</lastmod>")
    xml_content.append(f"    <changefreq>{url['changefreq']}</changefreq>")
    xml_content.append(f"    <priority>{url['priority']}</priority>")
    xml_content.append("  </url>")

xml_content.append("</urlset>")

with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(xml_content))

print(f"Sitemap successfully generated at {SITEMAP_FILE}!")
