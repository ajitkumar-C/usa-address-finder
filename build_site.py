import os
import csv
import json
import urllib.request
import re
import zipfile
import io

# Constants
CSV_URL = "https://raw.githubusercontent.com/scpike/us-state-county-zip/master/geo-data.csv"
CSV_FILE = "geo-data.csv"
GEONAMES_URL = "http://download.geonames.org/export/zip/US.zip"
GEONAMES_ZIP = "US.zip"
DIST_DIR = "."
STATE_DIR = os.path.join(DIST_DIR, "state")
COUNTY_DIR = os.path.join(DIST_DIR, "county")
DATA_DIR = os.path.join(DIST_DIR, "data")
JS_DIR = os.path.join(DIST_DIR, "js")
CSS_DIR = os.path.join(DIST_DIR, "css")

# Ensure directories exist
for d in [STATE_DIR, COUNTY_DIR, DATA_DIR, JS_DIR, CSS_DIR]:
    os.makedirs(d, exist_ok=True)

# Helper to slugify strings
def make_slug(name):
    slug = name.lower()
    # Replace non-alphanumeric with hyphen
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens and double hyphens
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug

# Download CSV if not exists
if not os.path.exists(CSV_FILE):
    print("Downloading dataset...")
    try:
        urllib.request.urlretrieve(CSV_URL, CSV_FILE)
        print("Dataset downloaded successfully.")
    except Exception as e:
        print("Error downloading dataset:", e)
        exit(1)
else:
    print("Using local geo-data.csv copy.")

# Download GeoNames coordinates if not exists
if not os.path.exists(GEONAMES_ZIP):
    print("Downloading GeoNames US zip codes coordinates...")
    try:
        urllib.request.urlretrieve(GEONAMES_URL, GEONAMES_ZIP)
        print("GeoNames dataset downloaded successfully.")
    except Exception as e:
        print("Error downloading GeoNames dataset:", e)
else:
    print("Using local US.zip coordinates copy.")

geonames_coords = {}
if os.path.exists(GEONAMES_ZIP):
    try:
        with zipfile.ZipFile(GEONAMES_ZIP) as zf:
            with zf.open("US.txt") as f:
                for line in f.read().decode('utf-8').splitlines():
                    parts = line.split('\t')
                    if len(parts) >= 11:
                        z_code = parts[1]
                        try:
                            lat = float(parts[9])
                            lon = float(parts[10])
                            geonames_coords[z_code] = (lat, lon)
                        except ValueError:
                            pass
        print(f"Loaded {len(geonames_coords)} coordinates from GeoNames.")
    except Exception as e:
        print("Error reading GeoNames ZIP:", e)

# Process CSV data
states_data = {}
zip_index = {}
all_counties = {}

# We need to compile:
# - States mapping: name, abbreviation, slug, count of counties, count of zips
# - Counties list for search index
# - State pages: list of counties and cities
# - County pages: list of zips grouped by city
print("Processing data...")
with open(CSV_FILE, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        state_fips = row['state_fips']
        state = row['state']
        abbr = row['state_abbr']
        zipcode = row['zipcode']
        county = row['county']
        city = row['city']
        
        if not state or not abbr or not zipcode or not county:
            continue
            
        state_slug = make_slug(state)
        county_slug = make_slug(county)
        county_key = f"{abbr.lower()}-{county_slug}"
        
        # Build states tree
        if state not in states_data:
            states_data[state] = {
                'name': state,
                'abbr': abbr,
                'fips': state_fips,
                'slug': state_slug,
                'counties': {},
                'total_zips': 0
            }
            
        state_entry = states_data[state]
        
        if county not in state_entry['counties']:
            state_entry['counties'][county] = {
                'name': county,
                'slug': county_slug,
                'key': county_key,
                'cities': {},
                'total_zips': 0
            }
            
        county_entry = state_entry['counties'][county]
        
        if city not in county_entry['cities']:
            county_entry['cities'][city] = []
            
        county_entry['cities'][city].append(zipcode)
        county_entry['total_zips'] += 1
        state_entry['total_zips'] += 1
        
        # Populate ZIP index for search
        lat, lon = geonames_coords.get(zipcode, (None, None))
        zip_index[zipcode] = [abbr, county, city, lat, lon]
        
        # Populate unique counties for index
        all_counties[county_key] = {
            'n': county,
            'a': abbr,
            's': county_key,
            'st': state
        }

print(f"Total states: {len(states_data)}")
print(f"Total ZIP codes parsed: {len(zip_index)}")
print(f"Total unique counties: {len(all_counties)}")

# Generate Search Index JSON
search_index = {
    'states': [
        {'n': s['name'], 'a': s['abbr'], 's': s['slug']}
        for s in sorted(states_data.values(), key=lambda x: x['name'])
    ],
    'counties': [
        {'n': c['n'], 'a': c['a'], 's': c['s'], 'st': c['st']}
        for c in sorted(all_counties.values(), key=lambda x: (x['a'], x['n']))
    ],
    'zips': zip_index
}

with open(os.path.join(DATA_DIR, "search-index.json"), "w", encoding="utf-8") as f:
    json.dump(search_index, f, separators=(',', ':'))
print("Search index JSON saved.")

# -----------------------------------------------
# PER-PAGE SEO METADATA (mirrors schema.js in FinanceCalculator)
# -----------------------------------------------
PAGE_SEO = {
    'homepage': {
        'keywords': 'usa zip code lookup, us address finder, zip code finder, united states postal codes, us zip codes by state, city zip code lookup, county zip codes, free us address search',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'state': {
        'keywords': 'state zip codes, county zip codes, cities by zip code, usa zip code list, state postal codes, zip codes by state, us postal code directory',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'county': {
        'keywords': 'county zip codes, zip codes by county, city zip codes, us postal codes, zip code list county, county postal codes usa',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'distance': {
        'keywords': 'zip code distance calculator, distance between zip codes, miles between zip codes, zip code mileage calculator, us zip code distance, postal code distance tool',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'radius': {
        'keywords': 'zip codes within radius, zip code radius finder, zip codes near me, zip codes within 25 miles, postal codes by radius, radius zip code search, zip codes in radius csv',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'generator': {
        'keywords': 'random us address generator, fake us address, fake zip code us, random us address for testing, generate us address, valid us address test, fake american address generator',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'standardizer': {
        'keywords': 'usps address standardizer, usps address format, us address format, address validation tool, standardize us address, usps address lookup, correct address format usa',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'compare': {
        'keywords': 'zip code comparison, compare zip codes, zip code info lookup, us zip code compare, postal code details, zip code side by side comparison',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'timezone': {
        'keywords': 'zip code time zone, us time zone by zip, timezone lookup zip code, what timezone is my zip code, zip code to timezone, find timezone by zip code',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'area_codes': {
        'keywords': 'area code lookup, us area codes, phone area code finder, area code by zip code, us telephone area codes, area code directory usa',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'virtual_address': {
        'keywords': 'virtual us address, usa virtual address, us virtual mailbox, package forwarding usa, reship us packages, tax free states usa, no sales tax states shipping',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'about': {
        'keywords': 'about usa address finder, us zip code database, us postal database, about us address tool, usa geographic data',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'contact': {
        'keywords': 'contact usa address finder, support us address finder, feedback zip code tool',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'privacy': {
        'keywords': 'privacy policy usa address finder, data policy zip code tool, cookie policy us address',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
    'disclaimer': {
        'keywords': 'disclaimer usa address finder, data accuracy zip codes, usps disclaimer postal data',
        'og_image': 'https://usa-address-zip.vercel.app/favicon.ico',
    },
}

SITE_OG_IMAGE = "https://usa-address-zip.vercel.app/favicon.ico"

# HTML Base Template Components
HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <meta name="author" content="USA Address Finder">
    <meta name="google-site-verification" content="p-8wt0DNXh9djTp1qFiyK1ZKc3vqq8Z_zhahqzWFLJ8" />
    <!-- Canonical Link -->
    <link rel="canonical" href="{canonical_url}">
    <!-- Open Graph Tags (Facebook, LinkedIn, WhatsApp sharing) -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:site_name" content="USA Address Finder">
    <!-- Twitter / X Card Tags -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{og_image}">
    <!-- Google Analytics placeholder: replace G-XXXXXXXXXX with your Measurement ID when ready -->
    <!-- <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-XXXXXXXXXX');
    </script> -->
    <link rel="stylesheet" href="{root_path}css/style.css?v=3">
    <!-- Google Schema Markup -->
    {schema_markup}
</head>
<body>
    <header>
        <div class="container nav-container">
            <a href="{root_path}index.html" class="logo">
                <svg class="flag-icon" width="34" height="22" viewBox="0 0 74 39" style="border-radius: 2px; box-shadow: var(--shadow-sm); border: 1px solid #112e51; display: inline-block; vertical-align: middle;">
                    <rect width="74" height="39" fill="#B22234"/>
                    <path d="M0,3h74M0,9h74M0,15h74M0,21h74M0,27h74M0,33h74" stroke="#FFFFFF" stroke-width="3"/>
                    <rect width="30" height="21" fill="#3C3B6E"/>
                    <g fill="#FFFFFF">
                        <circle cx="6" cy="5" r="1"/>
                        <circle cx="15" cy="5" r="1"/>
                        <circle cx="24" cy="5" r="1"/>
                        <circle cx="10" cy="10.5" r="1"/>
                        <circle cx="20" cy="10.5" r="1"/>
                        <circle cx="6" cy="16" r="1"/>
                        <circle cx="15" cy="16" r="1"/>
                        <circle cx="24" cy="16" r="1"/>
                    </g>
                </svg>
                <span>USA Address Finder</span>
            </a>
            <nav style="display: flex; align-items: center; gap: 12px;">
                <ul class="nav-links">
                    <li class="nav-close-wrapper">
                        <button id="menu-close" class="menu-close-btn" aria-label="Close Navigation Menu">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </li>
                    <li><a href="{root_path}index.html">Home</a></li>
                    <li class="nav-dropdown">
                        <a href="#" class="dropdown-trigger" style="display: flex; align-items: center; gap: 4px;">
                            <span>Tools</span>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                        </a>
                        <ul class="dropdown-menu">
                            <li><a href="{root_path}distance.html">📏 Distance Calculator</a></li>
                            <li><a href="{root_path}radius-finder.html">⭕ Radius Finder</a></li>
                            <li><a href="{root_path}address-generator.html">🎲 Address Generator</a></li>
                            <li><a href="{root_path}address-standardizer.html">📝 USPS Standardizer</a></li>
                            <li><a href="{root_path}compare.html">📊 ZIP Code Compare</a></li>
                            <li><a href="{root_path}timezone.html">🕒 Time Zone Finder</a></li>
                            <li><a href="{root_path}area-codes.html">📞 Area Code Lookup</a></li>
                            <li><a href="{root_path}virtual-address.html">📧 Virtual US Address</a></li>
                        </ul>
                    </li>
                    <li><a href="{root_path}about.html">About</a></li>
                    <li><a href="{root_path}contact.html">Contact</a></li>
                </ul>
                <button id="theme-toggle" class="theme-toggle-btn" title="Toggle Light/Dark Mode">
                    <!-- Sun Icon -->
                    <svg class="sun-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
                    <!-- Moon Icon -->
                    <svg class="moon-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display: none;"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
                </button>
                <button id="menu-toggle" class="menu-toggle-btn" aria-label="Toggle Navigation Menu" title="Toggle Navigation Menu">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
            </nav>
            <div id="nav-overlay" class="nav-overlay"></div>
        </div>
    </header>
"""

BREADCRUMBS_HTML = """
    <div class="container">
        <ul class="breadcrumbs">
            {breadcrumbs}
        </ul>
    </div>
"""

SIDEBAR_HTML = """
            <div class="sidebar">
                <!-- AdSense Top Sidebar Placement -->
                <div class="ad-card">
                    <div class="ad-label">Advertisement</div>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="20" x="2" y="2" rx="2"/><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    <div class="ad-placeholder-text">Support this website by enabling ads</div>
                </div>

                <!-- Premium Affiliate Lead Gen Card -->
                <div class="widget-card">
                    <h3 class="widget-title">Need to Move?</h3>
                    <p class="widget-text">Compare free moving quotes from certified local movers in your region. Save up to 40% on your next move!</p>
                    <a href="https://www.movingcompanyreviews.com" target="_blank" rel="noopener noreferrer" class="widget-btn">Get Free Moving Quotes</a>
                </div>

                <!-- Database Export Call to Action -->
                <div class="widget-card" style="background-image: linear-gradient(180deg, transparent, rgba(245, 158, 11, 0.04));">
                    <h3 class="widget-title" style="color: var(--accent-color);">USA ZIP Codes Database</h3>
                    <p class="widget-text">Get a clean, fully offline CSV/JSON version of the complete USA State-County-City-ZIP database.</p>
                    <a href="https://gumroad.com" target="_blank" rel="noopener noreferrer" class="widget-btn" style="background: var(--accent-gradient);">Download Dataset</a>
                </div>

                <!-- AdSense Bottom Sidebar Placement -->
                <div class="ad-card">
                    <div class="ad-label">Advertisement</div>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="20" x="2" y="2" rx="2"/><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    <div class="ad-placeholder-text">Sponsored Link</div>
                </div>
            </div>
"""

FOOTER = """
    <footer id="site-footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-col">
                    <h3 style="color: #ffffff; display: inline-block;">USA Address Finder</h3>
                    <p style="font-size: 13px; margin-top: 10px; color: #a3b8cc;">
                        A comprehensive, lightning-fast static directory of all 50 states, counties, and postal codes in the United States of America. Built for optimal speed, search indexing, and simple navigability.
                    </p>
                </div>
                <div class="footer-col">
                    <h3>Popular States</h3>
                    <ul>
                        <li><a href="{root_path}state/california.html">California</a></li>
                        <li><a href="{root_path}state/texas.html">Texas</a></li>
                        <li><a href="{root_path}state/new-york.html">New York</a></li>
                        <li><a href="{root_path}state/florida.html">Florida</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Legal & Info</h3>
                    <ul>
                        <li><a href="{root_path}about.html">About Us</a></li>
                        <li><a href="{root_path}contact.html">Contact Me</a></li>
                        <li><a href="{root_path}privacy.html">Privacy Policy</a></li>
                        <li><a href="{root_path}disclaimer.html">Disclaimer</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h3>Resources</h3>
                    <ul>
                        <li><a href="{root_path}index.html">Home Search</a></li>
                        <li><a href="{root_path}distance.html">Distance Calculator</a></li>
                        <li><a href="{root_path}radius-finder.html">Radius Finder</a></li>
                        <li><a href="{root_path}address-generator.html">Address Generator</a></li>
                        <li><a href="{root_path}address-standardizer.html">USPS Standardizer</a></li>
                        <li><a href="{root_path}compare.html">ZIP Compare</a></li>
                        <li><a href="{root_path}timezone.html">Time Zone Finder</a></li>
                        <li><a href="{root_path}area-codes.html">Area Code Lookup</a></li>
                        <li><a href="{root_path}sitemap.xml">XML Sitemap</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <div>&copy; 2026 USA Address Finder. All rights reserved. Built with SEO best practices.</div>
                <div>Data Source: US Census ZCTA Database</div>
            </div>
        </div>
    </footer>

    <!-- Copy to Clipboard Toast Alert -->
    <div id="copy-toast" class="toast">
        <svg class="toast-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <span id="toast-message">ZIP Code Copied!</span>
    </div>

    <script src="{root_path}js/search.js?v=3"></script>
</body>
</html>
"""

# -----------------
# 1. GENERATE HOMEPAGE (index.html)
# -----------------
def generate_homepage():
    title = "USA Address Finder - Free U.S. ZIP Code Lookup, Cities & States"
    description = "Free U.S. ZIP code finder & address lookup tool. Search 33,000+ postal codes by city, county, or state. Features distance calculators, radius search, and address generators."
    canonical_url = "https://usa-address-zip.vercel.app/"
    seo = PAGE_SEO['homepage']

    # Full @graph schema — mirrors RupeeBuddy pattern exactly
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": "https://usa-address-zip.vercel.app/#website",
                "url": "https://usa-address-zip.vercel.app/",
                "name": "USA Address Finder",
                "alternateName": ["USA Address Finder", "US ZIP Code Finder"],
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": "https://usa-address-zip.vercel.app/index.html?q={search_term_string}"
                    },
                    "query-input": "required name=search_term_string"
                },
                "publisher": {
                    "@id": "https://usa-address-zip.vercel.app/#organization"
                }
            },
            {
                "@type": "Organization",
                "@id": "https://usa-address-zip.vercel.app/#organization",
                "name": "USA Address Finder",
                "url": "https://usa-address-zip.vercel.app/",
                "logo": {
                    "@type": "ImageObject",
                    "@id": "https://usa-address-zip.vercel.app/#logo",
                    "url": "https://usa-address-zip.vercel.app/favicon.ico",
                    "caption": "USA Address Finder Logo"
                },
                "image": {"@id": "https://usa-address-zip.vercel.app/#logo"},
                "description": "USA Address Finder is a free, lightning-fast static directory of all U.S. states, counties, cities, and ZIP codes — with tools for distance calculation, radius search, address generation, and USPS standardization."
            }
        ]
    }
    schema_markup = f'<script type="application/ld+json">{json.dumps(schema_data)}</script>'
    
    # State Grid Items & Map Tiles HTML
    state_items_html = ""
    map_tiles_html = ""
    for state_name, data in sorted(states_data.items()):
        total_counties = len(data['counties'])
        state_items_html += f"""
        <a href="state/{data['slug']}.html" class="state-card">
            <div class="state-header">
                <div class="state-name">{state_name}</div>
                <div class="state-abbr">{data['abbr']}</div>
            </div>
            <div class="state-stats">
                <div class="stat-item">
                    <span class="stat-val">{total_counties}</span>
                    <span class="stat-lbl">Counties</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val">{data['total_zips']:,}</span>
                    <span class="stat-lbl">ZIP Codes</span>
                </div>
            </div>
        </a>
        """
        
        map_tiles_html += f"""
        <a href="state/{data['slug']}.html" class="map-tile-btn" data-name="{state_name}" data-abbr="{data['abbr']}" data-counties="{total_counties}" data-zips="{data['total_zips']:,}" style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; padding: 8px 4px; text-align: center; text-decoration: none; color: var(--text-primary); transition: all 0.2s ease; cursor: pointer; display: block;">
            <div style="font-weight: 700; font-size: 13px; color: var(--primary-color);">{data['abbr']}</div>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">{total_counties} Cty</div>
        </a>
        """

    # Assemble Homepage Body
    body_content = f"""
    <main class="hero animate-fade-in">
        <div class="container">
            <h1>Free <span>USA Address Finder</span> & U.S. ZIP Code Directory</h1>
            <p>Instant U.S. ZIP code lookup by address, city, county, or state. Calculate distance between postal codes, search radius maps, and format addresses to USPS standards.</p>
            
            <div class="search-wrapper">
                <div class="search-bar-container">
                    <div class="search-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                    </div>
                    <input type="text" id="global-search" class="search-input" placeholder="Search by ZIP, State, County, or City..." autocomplete="off">
                    <span class="kbd-shortcut">/</span>
                    <button id="clear-search" class="clear-search-btn">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                    </button>
                    <button class="search-btn" id="search-action-btn">Search</button>
                </div>
                <div id="suggestions" class="suggestions-box"></div>
                <div style="margin-top: 14px; text-align: center;">
                    <button id="geo-search-btn" class="geo-btn" title="Detect Location & Find ZIP Code">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><line x1="2" y1="12" x2="22" y2="12"/><line x1="12" y1="2" x2="12" y2="22"/><circle cx="12" cy="12" r="6"/></svg>
                        <span>Find ZIP Codes Near Me</span>
                    </button>
                </div>
            </div>
        </div>
    </main>

    <div class="container animate-fade-in" style="margin-top: 20px;">
        <!-- Home Ad Slot -->
        <div class="ad-card" style="min-height: 120px; margin-bottom: 24px;">
            <div class="ad-label">Advertisement</div>
            <div class="ad-placeholder-text">Ad Slot - Banner (Responsive)</div>
        </div>

        <!-- Interactive US State Explorer Map Widget -->
        <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 30px; box-shadow: var(--shadow-sm);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;">
                <div>
                    <h3 style="font-size: 18px; color: var(--text-primary); margin: 0 0 4px 0;">Interactive US State Explorer Map</h3>
                    <p style="font-size: 13.5px; color: var(--text-secondary); margin: 0;">Hover or select any US state tile below to inspect county counts and ZIP code coverage.</p>
                </div>
                <div id="map-state-badge" style="background: var(--accent-gradient); color: #fff; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 13px; display: inline-flex; align-items: center; gap: 6px;">
                    <span>Hover a State</span>
                </div>
            </div>
            
            <div id="us-map-tiles-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(58px, 1fr)); gap: 8px; margin-top: 16px;">
                {map_tiles_html}
            </div>
        </div>

        <h2 class="section-title">Explore by State Directory</h2>
        <div class="states-grid">
            {state_items_html}
        </div>
    </div>
    """
    
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=schema_markup,
                         keywords=seo['keywords'], canonical_url=canonical_url, og_image=seo['og_image'])
    html += body_content
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated index.html")

# -----------------
# 2. GENERATE STATE PAGES (state/[state-slug].html)
# -----------------
def generate_state_pages():
    for state_name, data in states_data.items():
        title = f"{state_name} ZIP Code USA - List of Cities & Counties ({data['abbr']})"
        description = f"Search the complete {state_name} ZIP code USA list. Find all cities, counties, and postal codes in {state_name} ({data['abbr']}). Download state ZIP codes CSV and view maps."
        
        breadcrumbs_list = f'<li><a href="../index.html">Home</a></li><li class="active">{state_name}</li>'
        breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
        
        state_canonical = f"https://usa-address-zip.vercel.app/state/{data['slug']}.html"
        seo = PAGE_SEO['state']
        state_keywords = f"{state_name} zip codes, {data['abbr']} zip code list, {state_name} counties, {state_name} postal codes, {seo['keywords']}"

        # AdministrativeArea + BreadcrumbList schema
        schema_list = [
            {
                "@context": "https://schema.org",
                "@type": "AdministrativeArea",
                "name": state_name,
                "alternateName": data['abbr'],
                "description": f"State of {state_name} with {len(data['counties'])} counties and {data['total_zips']} ZIP codes.",
                "identifier": data['fips'],
                "url": state_canonical
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://usa-address-zip.vercel.app/"},
                    {"@type": "ListItem", "position": 2, "name": f"{state_name} ZIP Codes", "item": state_canonical}
                ]
            }
        ]
        schema_markup = "".join([f'<script type="application/ld+json">{json.dumps(s)}</script>' for s in schema_list])

        # Create counties HTML grid items
        county_items_html = ""
        for county_name, county_data in sorted(data['counties'].items()):
            total_cities = len(county_data['cities'])
            county_items_html += f"""
            <a href="../county/{county_data['key']}.html" class="list-item-card" data-name="{county_name.lower()}">
                <span class="list-item-title">{county_name} County</span>
                <span class="list-item-count">{county_data['total_zips']} ZIPs</span>
            </a>
            """
            
        body_content = f"""
        <div class="container animate-fade-in">
            <div class="detail-layout">
                <div class="main-content">
                    <div class="state-info-header">
                        <div class="state-title-wrap">
                            <span class="state-badge-large">{data['abbr']}</span>
                            <h2>{state_name} ZIP Code USA Directory</h2>
                        </div>
                        <span style="font-size: 14px; color: var(--text-muted); font-weight: 600;">FIPS Code: {data['fips']}</span>
                    </div>
                    
                    <p style="margin: 0 0 24px 0; font-size: 15px; color: var(--text-secondary); line-height: 1.6;">
                        Explore our comprehensive U.S. postal database to search all cities, counties, and ZIP codes in {state_name}. 
                        Filter the listing by county below, or export the complete {state_name} ZIP code list to a CSV spreadsheet.
                    </p>

                    <div class="state-meta-stats">
                        <div class="meta-stat">
                            <div class="meta-val">{len(data['counties'])}</div>
                            <div class="meta-lbl">Counties</div>
                        </div>
                        <div class="meta-stat">
                            <div class="meta-val">{data['total_zips']:,}</div>
                            <div class="meta-lbl">Total ZIPs</div>
                        </div>
                        <div class="meta-stat">
                            <div class="meta-val">United States</div>
                            <div class="meta-lbl">Country</div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; flex-wrap: wrap; gap: 16px;">
                        <div class="filter-box" style="margin-bottom: 0; flex: 1; min-width: 250px;">
                            <h3 style="font-size: 16px; margin-bottom: 8px;">Filter Counties</h3>
                            <input type="text" id="county-filter" class="filter-input" placeholder="Type county name to filter...">
                        </div>
                        <button class="pill-btn active state-csv-btn" data-state-abbr="{data['abbr']}" data-state-name="{state_name}" style="padding: 10px 18px; display: inline-flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13px; height: 42px; cursor: pointer;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                            <span>Download State ZIPs (CSV)</span>
                        </button>
                    </div>

                    <div class="list-group" id="county-list">
                        {county_items_html}
                    </div>
                </div>
                {SIDEBAR_HTML}
            </div>
        </div>
        """
        
        html = HEADER.format(title=title, description=description, root_path="../", schema_markup=schema_markup,
                             keywords=state_keywords, canonical_url=state_canonical, og_image=seo['og_image'])
        html += breadcrumbs_html
        html += body_content
        html += FOOTER.format(root_path="../")
        
        filepath = os.path.join(STATE_DIR, f"{data['slug']}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
            
    print(f"Generated {len(states_data)} state detail pages.")

# -----------------
# 3. GENERATE COUNTY PAGES (county/[state-abbr]-[county-slug].html)
# -----------------
def generate_county_pages():
    total_counties_built = 0
    for state_name, state_data in states_data.items():
        for county_name, county_data in state_data['counties'].items():
            title = f"{county_name} County ZIP Codes, {state_name} ({state_data['abbr']})"
            description = f"Browse all ZIP codes in {county_name} County, {state_name} ({state_data['abbr']}). Filter postal codes by city, view coordinates, and download county ZIP code list CSV."
            
            breadcrumbs_list = f'<li><a href="../index.html">Home</a></li><li><a href="../state/{state_data["slug"]}.html">{state_name}</a></li><li class="active">{county_name} County</li>'
            breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
            
            county_canonical = f"https://usa-address-zip.vercel.app/county/{county_data['key']}.html"
            seo_county = PAGE_SEO['county']
            county_keywords = f"{county_name} County zip codes, {county_name} {state_name} postal codes, {state_data['abbr']} county zip list, {seo_county['keywords']}"

            # AdministrativeArea + BreadcrumbList schema
            schema_list = [
                {
                    "@context": "https://schema.org",
                    "@type": "AdministrativeArea",
                    "name": f"{county_name} County",
                    "containedInPlace": {"@type": "AdministrativeArea", "name": state_name},
                    "description": f"County of {county_name} located in {state_name} with {county_data['total_zips']} ZIP codes.",
                    "url": county_canonical
                },
                {
                    "@context": "https://schema.org",
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://usa-address-zip.vercel.app/"},
                        {"@type": "ListItem", "position": 2, "name": f"{state_name} ZIP Codes", "item": f"https://usa-address-zip.vercel.app/state/{state_data['slug']}.html"},
                        {"@type": "ListItem", "position": 3, "name": f"{county_name} County ZIP Codes", "item": county_canonical}
                    ]
                }
            ]
            schema_markup = "".join([f'<script type="application/ld+json">{json.dumps(s)}</script>' for s in schema_list])

            # Generate ZIP codes grouped by city
            zips_by_city_html = ""
            for city_name, zip_list in sorted(county_data['cities'].items()):
                city_slug = make_slug(city_name)
                zip_cards_html = ""
                for z in sorted(zip_list):
                    zip_cards_html += f"""
                    <div class="zip-card" onclick="copyZipCode('{z}')">
                        <span class="zip-code-text">{z}</span>
                        <span class="zip-city-text">{city_name}</span>
                        <button class="copy-btn" title="Copy ZIP code">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                        </button>
                    </div>
                    """
                zips_by_city_html += f"""
                <div class="city-section" data-city="{city_name.lower()}" data-city-slug="{city_slug}">
                    <h4 class="city-group-title">{city_name} ({len(zip_list)} ZIPs)</h4>
                    <div class="zip-grid">
                        {zip_cards_html}
                    </div>
                </div>
                """

            # Generate pill filters for cities
            city_pills_html = '<div class="pill-filters" style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px;">'
            city_pills_html += '<button class="pill-btn active" onclick="filterByPill(\'all\', this)">All Cities</button>'
            for city_name in sorted(county_data['cities'].keys()):
                city_slug = make_slug(city_name)
                city_pills_html += f'<button class="pill-btn" onclick="filterByPill(\'{city_slug}\', this)">{city_name}</button>'
            city_pills_html += '</div>'

            body_content = f"""
            <div class="container animate-fade-in">
                <div class="detail-layout">
                    <div class="main-content">
                        <div class="state-info-header">
                            <div class="state-title-wrap">
                                <span class="state-badge-large" style="background: var(--accent-gradient);">{state_data['abbr']}</span>
                                <h2>{county_name} County</h2>
                            </div>
                            <span style="font-size: 14px; color: var(--text-muted); font-weight: 600;">{state_name}</span>
                        </div>

                        <div class="state-meta-stats">
                            <div class="meta-stat">
                                <div class="meta-val">{county_data['total_zips']}</div>
                                <div class="meta-lbl">ZIP Codes</div>
                            </div>
                            <div class="meta-stat">
                                <div class="meta-val">{len(county_data['cities'])}</div>
                                <div class="meta-lbl">Cities/Towns</div>
                            </div>
                            <div class="meta-stat">
                                <div class="meta-val">{state_data['abbr']}</div>
                                <div class="meta-lbl">State</div>
                            </div>
                        </div>

                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 16px;">
                            <div class="filter-box" style="margin-bottom: 0; flex: 1; min-width: 250px;">
                                <h3 style="font-size: 16px; margin-bottom: 8px;">Filter by City</h3>
                                <input type="text" id="city-filter" class="filter-input" placeholder="Type city name to filter ZIP codes...">
                                {city_pills_html}
                            </div>
                            <button class="pill-btn active county-csv-btn" data-state-abbr="{state_data['abbr']}" data-county-name="{county_name}" style="padding: 10px 18px; display: inline-flex; align-items: center; gap: 8px; font-weight: 600; font-size: 13px; height: 42px; cursor: pointer; margin-top: 24px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                                <span>Download County ZIPs (CSV)</span>
                            </button>
                        </div>

                        <div id="zip-sections-container">
                            {zips_by_city_html}
                        </div>
                    </div>
                    {SIDEBAR_HTML}
                </div>
            </div>
            """
            
            html = HEADER.format(title=title, description=description, root_path="../", schema_markup=schema_markup,
                                 keywords=county_keywords, canonical_url=county_canonical, og_image=seo_county['og_image'])
            html += breadcrumbs_html
            html += body_content
            html += FOOTER.format(root_path="../")
            
            filepath = os.path.join(COUNTY_DIR, f"{county_data['key']}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            total_counties_built += 1
            
    print(f"Generated {total_counties_built} county detail pages.")

def generate_info_pages():
    print("Generating info pages (about, contact, privacy, disclaimer)...")
    
    # 1. ABOUT US
    about_title = "About Us - USA Address Finder"
    about_desc = "Learn about USA Address Finder, our data sources, features, and target objectives for our geographical tools."
    about_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">About Us</h2>
                <p style="margin-bottom: 16px; font-size: 16px; color: var(--text-secondary);">
                    Welcome to <strong>USA Address Finder</strong>! We provide a highly responsive, modern, and lightning-fast directory of United States geographical data. Our platform lets citizens, developers, and researchers browse and search across all 50 states, counties, cities, and zip codes.
                </p>
                <h3 style="margin: 24px 0 12px 0; font-family: var(--font-heading); font-size: 20px;">Our Mission</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    We aim to build the fastest, cleanest, and most user-friendly lookup tool for U.S. postal codes and geographic areas. Unlike heavy, slow databases, our static-page design yields rapid page loads (typically under 100ms) and is optimized for search engines to index, ensuring you get accurate, quick results.
                </p>
                <h3 style="margin: 24px 0 12px 0; font-family: var(--font-heading); font-size: 20px;">Data Reliability</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    Our data is compiled directly from public U.S. Census ZCTA (ZIP Code Tabulation Areas) records, providing high-precision administrative details for counties and municipalities across America.
                </p>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    _seo_about = PAGE_SEO['about']
    _about_schema = {"@context": "https://schema.org", "@type": "AboutPage", "name": about_title, "description": about_desc, "url": "https://usa-address-zip.vercel.app/about.html"}
    html = HEADER.format(title=about_title, description=about_desc, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_about_schema)}</script>',
                         keywords=_seo_about['keywords'], canonical_url="https://usa-address-zip.vercel.app/about.html", og_image=SITE_OG_IMAGE)
    html += about_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "about.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # 2. CONTACT ME
    contact_title = "Contact Me - Get in Touch"
    contact_desc = "Have questions, feedback, or database requests? Contact the USA Address Finder team."
    contact_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">Contact Me</h2>
                <p style="margin-bottom: 20px; font-size: 16px; color: var(--text-secondary);">
                    Have any questions, feedback, or database requests regarding USA Address Finder?
                </p>
                <p style="font-size: 18px; font-weight: 600; color: var(--primary-color); margin-bottom: 24px;">
                    To reach out to me, please email: <a href="mailto:ac962017@gmail.com">ac962017@gmail.com</a>
                </p>
                <p style="font-size: 14px; color: var(--text-muted);">
                    I generally respond to all inquiries within 24 to 48 hours.
                </p>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    _seo_contact = PAGE_SEO['contact']
    _contact_schema = {"@context": "https://schema.org", "@type": "ContactPage", "name": contact_title, "description": contact_desc, "url": "https://usa-address-zip.vercel.app/contact.html"}
    html = HEADER.format(title=contact_title, description=contact_desc, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_contact_schema)}</script>',
                         keywords=_seo_contact['keywords'], canonical_url="https://usa-address-zip.vercel.app/contact.html", og_image=SITE_OG_IMAGE)
    html += contact_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "contact.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # 3. PRIVACY POLICY
    privacy_title = "Privacy Policy - USA Address Finder"
    privacy_desc = "Privacy policy for USA Address Finder. Learn about how we handle user data and third-party advertising cookies."
    privacy_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">Privacy Policy</h2>
                <p style="margin-bottom: 16px; font-size: 14px; color: var(--text-muted);">Last Updated: July 12, 2026</p>
                
                <h3 style="margin: 20px 0 10px 0; font-size: 18px;">1. Information We Collect</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    Our website is designed as a public directory. We do not require registration or collect personal data from users browsing our geographic database. If you submit a contact form, the details you provide (name, email, and message) are used solely to reply to your inquiry.
                </p>

                <h3 style="margin: 20px 0 10px 0; font-size: 18px;">2. Cookies and Third-Party Ads</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    We may work with third-party advertising partners like <strong>Google AdSense</strong>. Google uses cookies to serve ads based on a user's prior visits to our website or other sites on the Internet. Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to our site.
                </p>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    Users may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google Ads Settings</a>.
                </p>

                <h3 style="margin: 20px 0 10px 0; font-size: 18px;">3. Log Files</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    Like most standard websites, we utilize basic server logs which include internet protocol (IP) addresses, browser type, internet service provider (ISP), referring/exit pages, and click counts to analyze trends and administer the site.
                </p>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    _seo_privacy = PAGE_SEO['privacy']
    _privacy_schema = {"@context": "https://schema.org", "@type": "WebPage", "name": privacy_title, "description": privacy_desc, "url": "https://usa-address-zip.vercel.app/privacy.html"}
    html = HEADER.format(title=privacy_title, description=privacy_desc, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_privacy_schema)}</script>',
                         keywords=_seo_privacy['keywords'], canonical_url="https://usa-address-zip.vercel.app/privacy.html", og_image=SITE_OG_IMAGE)
    html += privacy_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "privacy.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # 4. DISCLAIMER
    disc_title = "Disclaimer - Data Accuracy Terms"
    disc_desc = "Disclaimer notice for USA Address Finder. Read our statements regarding data sources and information warranty."
    disc_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">Disclaimer</h2>
                <p style="margin-bottom: 16px; font-size: 14px; color: var(--text-muted);">Last Updated: July 12, 2026</p>
                
                <h3 style="margin: 20px 0 10px 0; font-size: 18px;">No Warranty of Accuracy</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    The geographic and postal data on <strong>USA Address Finder</strong> is provided for informational and search convenience purposes only. While we compile this database directly from official public records (U.S. Census ZCTA Database), we do not warrant that all ZIP code mappings are 100% error-free or fully up-to-date.
                </p>
                
                <h3 style="margin: 20px 0 10px 0; font-size: 18px;">Not an Official USPS Source</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    This website is an independent project and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with the United States Postal Service (USPS) or any other government entity. "ZIP Code" is a registered trademark of the USPS.
                </p>

                <h3 style="margin: 20px 0 10px 0; font-size: 18px;">Limitation of Liability</h3>
                <p style="margin-bottom: 16px; font-size: 15px; color: var(--text-secondary);">
                    Under no circumstances shall we be held liable for any loss, damage, or delivery delays resulting from the use of data found on this website. For critical mail delivery verification, please consult official resources at <a href="https://www.usps.com" target="_blank" rel="noopener">USPS.com</a>.
                </p>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    _seo_disc = PAGE_SEO['disclaimer']
    _disc_schema = {"@context": "https://schema.org", "@type": "WebPage", "name": disc_title, "description": disc_desc, "url": "https://usa-address-zip.vercel.app/disclaimer.html"}
    html = HEADER.format(title=disc_title, description=disc_desc, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_disc_schema)}</script>',
                         keywords=_seo_disc['keywords'], canonical_url="https://usa-address-zip.vercel.app/disclaimer.html", og_image=SITE_OG_IMAGE)
    html += disc_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "disclaimer.html"), "w", encoding="utf-8") as f:
        f.write(html)
        
    print("All info pages generated successfully.")

def generate_distance_page():
    print("Generating ZIP code distance page (distance.html)...")
    title = "ZIP Code Distance Calculator - Distance Between Two ZIP Codes"
    description = "Calculate exact straight-line distance between two U.S. ZIP codes in miles and kilometers. Free ZIP code mileage calculator with coordinates and Haversine formula."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Distance Calculator</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    # Body content of the distance page
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">ZIP Code Distance Calculator</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Calculate distance between two ZIP codes in miles and kilometers. Our free ZIP code mileage calculator uses coordinate centroids and the Haversine formula.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 30px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;" class="calc-inputs-grid">
                        <div class="calc-field" style="position: relative;">
                            <label for="zip1" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Origin ZIP Code</label>
                            <div class="search-bar-container" style="padding: 2px 2px 2px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary);">
                                <input type="text" id="zip1" class="search-input" placeholder="e.g. 90210" autocomplete="off" style="font-size: 14px; height: 38px;">
                                <button id="clear-zip1" class="clear-search-btn" style="padding: 4px; margin-right: 2px;">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                                </button>
                            </div>
                            <div id="suggestions-zip1" class="suggestions-box" style="top: 100%; max-height: 200px;"></div>
                        </div>
                        
                        <div class="calc-field" style="position: relative;">
                            <label for="zip2" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Destination ZIP Code</label>
                            <div class="search-bar-container" style="padding: 2px 2px 2px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary);">
                                <input type="text" id="zip2" class="search-input" placeholder="e.g. 10001" autocomplete="off" style="font-size: 14px; height: 38px;">
                                <button id="clear-zip2" class="clear-search-btn" style="padding: 4px; margin-right: 2px;">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                                </button>
                            </div>
                            <div id="suggestions-zip2" class="suggestions-box" style="top: 100%; max-height: 200px;"></div>
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <button id="calculate-btn" class="search-btn" style="padding: 12px 30px; font-size: 15px; width: 100%; max-width: 300px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m16 12-4-4-4 4M12 8v8"/></svg>
                            <span>Calculate Distance</span>
                        </button>
                    </div>
                </div>
                
                <div id="error-message" style="display: none; background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; border-radius: 6px; padding: 14px 20px; font-size: 14px; font-weight: 500; margin-bottom: 24px; align-items: center; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span id="error-text">Please enter valid ZIP codes.</span>
                </div>
                
                <div id="result-container" style="display: none;">
                    <div class="result-card" style="background: var(--bg-secondary); border: 2px solid var(--primary-color); border-radius: var(--card-radius); padding: 28px; box-shadow: var(--shadow-md); margin-bottom: 30px; position: relative; overflow: hidden;">
                        <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; background: var(--primary-gradient);"></div>
                        <h3 style="font-size: 18px; margin-bottom: 16px; text-align: center; color: var(--text-primary);">Calculation Results</h3>
                        
                        <div style="display: flex; justify-content: center; align-items: baseline; gap: 24px; flex-wrap: wrap; margin-bottom: 24px;">
                            <div style="text-align: center;">
                                <div id="dist-miles" style="font-family: var(--font-heading); font-size: 42px; font-weight: 800; color: var(--primary-color); line-height: 1;">0.0</div>
                                <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Miles</div>
                            </div>
                            <div style="font-family: var(--font-heading); font-size: 36px; font-weight: 300; color: var(--border-color); line-height: 1;" class="dist-divider">|</div>
                            <div style="text-align: center;">
                                <div id="dist-km" style="font-family: var(--font-heading); font-size: 42px; font-weight: 800; color: var(--accent-color); line-height: 1;">0.0</div>
                                <div style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-top: 4px;">Kilometers</div>
                            </div>
                        </div>

                        <!-- Interactive SVG Visual Connection -->
                        <div style="width: 100%; height: 80px; margin-bottom: 24px; display: flex; align-items: center; justify-content: center; background: var(--bg-tertiary); border-radius: 6px; border: 1px solid var(--border-color); padding: 0 30px; overflow: hidden;">
                            <svg width="100%" height="60" viewBox="0 0 400 60" preserveAspectRatio="none" style="max-width: 500px;">
                                <line x1="40" y1="30" x2="360" y2="30" stroke="var(--border-color)" stroke-width="3" stroke-dasharray="6,6" />
                                <path id="svg-arc" d="M 40 30 Q 200 10 360 30" fill="none" stroke="var(--primary-color)" stroke-width="3" stroke-linecap="round" />
                                
                                <circle cx="40" cy="30" r="8" fill="var(--primary-color)" />
                                <circle cx="40" cy="30" r="14" fill="none" stroke="var(--primary-color)" stroke-width="2" opacity="0.4">
                                    <animate attributeName="r" values="8;16;8" dur="3s" repeatCount="indefinite"/>
                                    <animate attributeName="opacity" values="0.6;0;0.6" dur="3s" repeatCount="indefinite"/>
                                </circle>
                                
                                <circle cx="360" cy="30" r="8" fill="var(--accent-color)" />
                                <circle cx="360" cy="30" r="14" fill="none" stroke="var(--accent-color)" stroke-width="2" opacity="0.4">
                                    <animate attributeName="r" values="8;16;8" dur="3s" repeatCount="indefinite" begin="1.5s"/>
                                    <animate attributeName="opacity" values="0.6;0;0.6" dur="3s" repeatCount="indefinite" begin="1.5s"/>
                                </circle>
                                
                                <text x="40" y="52" font-size="10" font-weight="700" fill="var(--text-primary)" text-anchor="middle" id="svg-zip1">ZIP 1</text>
                                <text x="360" y="52" font-size="10" font-weight="700" fill="var(--text-primary)" text-anchor="middle" id="svg-zip2">ZIP 2</text>
                            </svg>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;" class="calc-results-grid">
                            <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 16px;">
                                <div style="font-size: 11px; font-weight: 700; color: var(--primary-color); text-transform: uppercase; margin-bottom: 6px;">From (Origin)</div>
                                <h4 id="zip1-title" style="font-size: 16px; margin-bottom: 6px;">ZIP 1</h4>
                                <div id="zip1-detail" style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">City, County, State</div>
                                <div style="font-size: 12px; color: var(--text-muted); font-family: monospace;">Lat: <span id="zip1-lat">0.0</span>, Lon: <span id="zip1-lon">0.0</span></div>
                            </div>
                            
                            <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 16px;">
                                <div style="font-size: 11px; font-weight: 700; color: var(--accent-color); text-transform: uppercase; margin-bottom: 6px;">To (Destination)</div>
                                <h4 id="zip2-title" style="font-size: 16px; margin-bottom: 6px;">ZIP 2</h4>
                                <div id="zip2-detail" style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">City, County, State</div>
                                <div style="font-size: 12px; color: var(--text-muted); font-family: monospace;">Lat: <span id="zip2-lat">0.0</span>, Lon: <span id="zip2-lon">0.0</span></div>
                            </div>
                        </div>
                        
                        <div style="border-top: 1px solid var(--border-color); padding-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                            <span style="font-size: 13px; color: var(--text-muted);">Share this distance calculation:</span>
                            <div style="display: flex; gap: 8px; width: 100%; max-width: 380px;">
                                <input type="text" id="share-url" readonly style="flex: 1; border: 1px solid var(--border-color); border-radius: 4px; padding: 6px 10px; font-size: 12px; background: var(--bg-tertiary); color: var(--text-secondary); outline: none;" onclick="this.select()">
                                <button id="copy-share-btn" class="pill-btn active" style="font-size: 12px; padding: 6px 12px; white-space: nowrap;">Copy Link</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="faq-section" style="margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 30px;">
                    <h3 style="font-size: 18px; margin-bottom: 16px;">Frequently Asked Questions</h3>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">How is the distance calculated between two ZIP codes?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            We calculate the great-circle distance (straight-line distance "as the crow flies") using the Haversine formula based on geographic centroids of each ZIP code area.
                        </p>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">Is this the driving distance?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            No, this calculator measures straight-line distance. Driving distances will usually be 10% to 30% longer depending on road paths and terrain.
                        </p>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_dist = PAGE_SEO['distance']
    _dist_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/distance.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Straight-line distance in miles and kilometers", "Haversine formula calculation", "ZIP code coordinate lookup", "Shareable result URL"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_dist_schema)}</script>',
                         keywords=_seo_dist['keywords'], canonical_url="https://usa-address-zip.vercel.app/distance.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "distance.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated distance.html")

def generate_address_generator_page():
    print("Generating ZIP/State/City/County random address generator page (address-generator.html)...")
    title = "Random US Address Generator - Generate Valid Street Addresses & Fake ZIP Codes"
    description = "Generate random U.S. street addresses based on ZIP code, state, city, or county. Ideal for software developers requiring fake U.S. ZIP codes and valid test addresses."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Address Generator</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    # Body content of the address generator page
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">Random US Address Generator</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Need test data, a fake zip code, or a random U.S. address for validation tests? Select a geographic scope below (State, County, City, or ZIP code) or generate completely random valid U.S. street address options.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <div style="position: relative; margin-bottom: 20px;">
                        <label for="gen-search" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Filter by State, County, City, or ZIP Code</label>
                        <div class="search-bar-container" style="padding: 2px 2px 2px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary);">
                            <div class="search-icon" style="color: var(--text-muted); margin-right: 8px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                            </div>
                            <input type="text" id="gen-search" class="search-input" placeholder="Type State, County, City, or 5-digit ZIP..." autocomplete="off" style="font-size: 14px; height: 38px;">
                            <button id="clear-gen" class="clear-search-btn" style="padding: 4px; margin-right: 2px;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                            </button>
                        </div>
                        <div id="suggestions-gen" class="suggestions-box" style="top: 100%; max-height: 250px;"></div>
                    </div>
                    
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
                        <div id="active-scope" style="font-size: 14px; font-weight: 600; color: var(--text-secondary); display: flex; align-items: center; gap: 6px;">
                            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #34d399;"></span>
                            <span>Scope: <strong>United States (All)</strong></span>
                        </div>
                        
                        <button id="generate-btn" class="search-btn" style="padding: 10px 24px; font-size: 14px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                            <span>Generate 6 Addresses</span>
                        </button>
                    </div>
                </div>
                
                <div id="gen-error-message" style="display: none; background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; border-radius: 6px; padding: 14px 20px; font-size: 14px; font-weight: 500; margin-bottom: 24px; align-items: center; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span id="gen-error-text">Failed to generate addresses.</span>
                </div>
                
                <div id="addresses-container" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;" class="calc-results-grid">
                    <!-- Cards will be dynamically generated by Javascript -->
                </div>
                
                <div id="share-container" style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 20px; margin-bottom: 30px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; display: none;">
                    <span style="font-size: 13px; color: var(--text-muted); font-weight: 500;">Share this generator configuration:</span>
                    <div style="display: flex; gap: 8px; width: 100%; max-width: 420px;">
                        <input type="text" id="gen-share-url" readonly style="flex: 1; border: 1px solid var(--border-color); border-radius: 4px; padding: 6px 10px; font-size: 12px; background: var(--bg-tertiary); color: var(--text-secondary); outline: none;" onclick="this.select()">
                        <button id="gen-copy-share-btn" class="pill-btn active" style="font-size: 12px; padding: 6px 12px; white-space: nowrap;">Copy Link</button>
                    </div>
                </div>

                <div class="faq-section" style="margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 30px;">
                    <h3 style="font-size: 18px; margin-bottom: 16px;">Frequently Asked Questions</h3>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">Are these actual physical U.S. addresses?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            No. The geographic details (City, State, County, and ZIP code) are real data structures sourced from the U.S. Census Bureau. However, the street numbers and names are generated randomly using statistical naming patterns to preserve privacy.
                        </p>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">How do I get a list of valid US ZIP codes or fake address data for testing?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            Our generator lets you scope address details down to any specific ZIP code or city. You can generate multiple valid mock addresses with correctly formatted street names, counties, states, and coordinates to verify your databases, checkout fields, and APIs.
                        </p>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">What are these addresses useful for?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            They are valuable for developers, software testers, and database administrators who require realistic dummy U.S. contact details to test forms, validation libraries, or lookup systems.
                        </p>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_gen = PAGE_SEO['generator']
    _gen_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/address-generator.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Generate random US addresses", "Filter by state, county, city, or ZIP", "Realistic street name generation", "Copy address to clipboard"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_gen_schema)}</script>',
                         keywords=_seo_gen['keywords'], canonical_url="https://usa-address-zip.vercel.app/address-generator.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "address-generator.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated address-generator.html")

def generate_radius_page():
    print("Generating ZIP Code Radius Finder page (radius-finder.html)...")
    title = "ZIP Code Radius Finder - Search Postal Codes by Radius (CSV Download)"
    description = "Find all U.S. ZIP codes within a 5, 10, 25, 50, or 100 mile radius of any city or postal code. Sort results by distance and export zip code lists to CSV."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Radius Finder</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    # Body content of the radius finder page
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">ZIP Code Radius Finder</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Find all U.S. postal codes within a specific mileage radius of any starting ZIP code or city. Sort results by proximity and download the listing as a CSV spreadsheet.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px;" class="calc-results-grid">
                        <div style="position: relative;">
                            <label for="radius-origin" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Starting ZIP Code or City</label>
                            <div class="search-bar-container" style="padding: 2px 2px 2px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary);">
                                <div class="search-icon" style="color: var(--text-muted); margin-right: 8px;">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                                </div>
                                <input type="text" id="radius-origin" class="search-input" placeholder="Type 5-digit ZIP or City..." autocomplete="off" style="font-size: 14px; height: 38px;">
                                <button id="clear-radius" class="clear-search-btn" style="padding: 4px; margin-right: 2px;">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                                </button>
                            </div>
                            <div id="suggestions-radius" class="suggestions-box" style="top: 100%; max-height: 220px;"></div>
                        </div>
                        
                        <div>
                            <label for="radius-range" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Radius Distance</label>
                            <select id="radius-range" style="width: 100%; height: 44px; border: 1px solid var(--border-color); border-radius: 4px; padding: 0 12px; background: var(--bg-secondary); color: var(--text-primary); font-size: 14px; outline: none; cursor: pointer;">
                                <option value="5">5 Miles</option>
                                <option value="10" selected>10 Miles</option>
                                <option value="15">15 Miles</option>
                                <option value="25">25 Miles</option>
                                <option value="50">50 Miles</option>
                                <option value="100">100 Miles</option>
                            </select>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: flex-end;">
                        <button id="find-zips-btn" class="search-btn" style="padding: 10px 24px; font-size: 14px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                            <span>Search Radius</span>
                        </button>
                    </div>
                </div>
                
                <div id="radius-error-message" style="display: none; background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; border-radius: 6px; padding: 14px 20px; font-size: 14px; font-weight: 500; margin-bottom: 24px; align-items: center; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span id="radius-error-text">Failed to perform radius search.</span>
                </div>
                
                <div id="radius-results-wrapper" style="display: none; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                        <h3 id="radius-results-title" style="font-size: 16px; margin: 0; color: var(--text-primary);">ZIP Codes Found</h3>
                        <button id="radius-export-btn" class="pill-btn active" style="padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: 12px; cursor: pointer;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                            <span>Export to CSV</span>
                        </button>
                    </div>
                    
                    <div style="overflow-x: auto; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); box-shadow: var(--shadow-sm);">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                            <thead>
                                <tr style="border-bottom: 2px solid var(--border-color); background: var(--bg-tertiary);">
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 100px;">Distance</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 110px;">ZIP Code</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">City</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 90px;">State</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">County</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); font-family: monospace; font-size: 12px;">Coordinates</th>
                                </tr>
                            </thead>
                            <tbody id="radius-table-body">
                                <!-- Dynamically generated rows -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="faq-section" style="margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 30px;">
                    <h3 style="font-size: 18px; margin-bottom: 16px;">Frequently Asked Questions</h3>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">How is the radius distance calculated?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            We compute straight-line distance (as the crow flies) between the coordinate centroids of the starting location and target ZIP codes using the **Haversine formula**.
                        </p>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_radius = PAGE_SEO['radius']
    _radius_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/radius-finder.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Find ZIP codes within a radius", "Set custom mile or kilometer radius", "Export results to CSV", "Sort by distance"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_radius_schema)}</script>',
                         keywords=_seo_radius['keywords'], canonical_url="https://usa-address-zip.vercel.app/radius-finder.html", og_image=SITE_OG_IMAGE)
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Radius Finder</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    # Body content of the radius finder page
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">ZIP Code Radius Finder</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Find all U.S. postal codes within a specific mileage radius of any starting ZIP code or city. Sort results by proximity and download the listing as a CSV spreadsheet.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px;" class="calc-results-grid">
                        <div style="position: relative;">
                            <label for="radius-origin" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Starting ZIP Code or City</label>
                            <div class="search-bar-container" style="padding: 2px 2px 2px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary);">
                                <div class="search-icon" style="color: var(--text-muted); margin-right: 8px;">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                                </div>
                                <input type="text" id="radius-origin" class="search-input" placeholder="Type 5-digit ZIP or City..." autocomplete="off" style="font-size: 14px; height: 38px;">
                                <button id="clear-radius" class="clear-search-btn" style="padding: 4px; margin-right: 2px;">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
                                </button>
                            </div>
                            <div id="suggestions-radius" class="suggestions-box" style="top: 100%; max-height: 220px;"></div>
                        </div>
                        
                        <div>
                            <label for="radius-range" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Radius Distance</label>
                            <select id="radius-range" style="width: 100%; height: 44px; border: 1px solid var(--border-color); border-radius: 4px; padding: 0 12px; background: var(--bg-secondary); color: var(--text-primary); font-size: 14px; outline: none; cursor: pointer;">
                                <option value="5">5 Miles</option>
                                <option value="10" selected>10 Miles</option>
                                <option value="15">15 Miles</option>
                                <option value="25">25 Miles</option>
                                <option value="50">50 Miles</option>
                                <option value="100">100 Miles</option>
                            </select>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: flex-end;">
                        <button id="find-zips-btn" class="search-btn" style="padding: 10px 24px; font-size: 14px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; cursor: pointer;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                            <span>Search Radius</span>
                        </button>
                    </div>
                </div>
                
                <div id="radius-error-message" style="display: none; background: #fee2e2; border: 1px solid #fca5a5; color: #b91c1c; border-radius: 6px; padding: 14px 20px; font-size: 14px; font-weight: 500; margin-bottom: 24px; align-items: center; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    <span id="radius-error-text">Failed to perform radius search.</span>
                </div>
                
                <div id="radius-results-wrapper" style="display: none; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                        <h3 id="radius-results-title" style="font-size: 16px; margin: 0; color: var(--text-primary);">ZIP Codes Found</h3>
                        <button id="radius-export-btn" class="pill-btn active" style="padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: 12px; cursor: pointer;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                            <span>Export to CSV</span>
                        </button>
                    </div>
                    
                    <div style="overflow-x: auto; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); box-shadow: var(--shadow-sm);">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                            <thead>
                                <tr style="border-bottom: 2px solid var(--border-color); background: var(--bg-tertiary);">
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 100px;">Distance</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 110px;">ZIP Code</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">City</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 90px;">State</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">County</th>
                                    <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); font-family: monospace; font-size: 12px;">Coordinates</th>
                                </tr>
                            </thead>
                            <tbody id="radius-table-body">
                                <!-- Dynamically generated rows -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="faq-section" style="margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 30px;">
                    <h3 style="font-size: 18px; margin-bottom: 16px;">Frequently Asked Questions</h3>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">How is the radius distance calculated?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            We compute straight-line distance (as the crow flies) between the coordinate centroids of the starting location and target ZIP codes. This calculation uses the **Haversine formula** (spherical law of cosines) based on exact latitude and longitude values, giving accurate geodetic results.
                        </p>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">Can I filter by city names?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            Yes! You can type a city name (like "Houston" or "Miami") into the starting box, select it from the suggestions list, and the tool will calculate distances from that city's primary centroid to all surrounding ZIP codes.
                        </p>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_radius_schema)}</script>',
                         keywords=_seo_radius['keywords'], canonical_url="https://usa-address-zip.vercel.app/radius-finder.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "radius-finder.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated radius-finder.html")

def generate_standardizer_page():
    print("Generating USPS Address Standardizer page (address-standardizer.html)...")
    title = "USPS Address Standardizer - Format Address by USPS Publication 28"
    description = "Free online USPS address standardizer tool. Format unformatted U.S. street addresses to official USPS Publication 28 mailing standards and street abbreviations."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Address Standardizer</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">USPS Address Standardizer & Formatter</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Format messy or informal U.S. addresses to official USPS Publication 28 mailing standards. Convert text to uppercase, abbreviate street suffixes, directionals, and apartment/suite numbers automatically.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <label for="raw-address-input" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-primary);">Paste Raw or Unformatted U.S. Address</label>
                    <textarea id="raw-address-input" style="width: 100%; height: 110px; border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; font-size: 14px; background: var(--bg-secondary); color: var(--text-primary); outline: none; margin-bottom: 16px; font-family: inherit; resize: vertical;" placeholder="e.g. 123 west main street apartment 4b, beverly hills, california 90210"></textarea>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                        <button id="standardize-btn" class="search-btn" style="padding: 10px 24px; font-size: 14px; display: inline-flex; align-items: center; gap: 8px; cursor: pointer;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                            <span>Standardize Address</span>
                        </button>
                        <button id="sample-address-btn" class="pill-btn" style="padding: 8px 16px; font-size: 12px; cursor: pointer;">Insert Sample Address</button>
                    </div>
                </div>
                
                <div id="standardizer-result-wrapper" style="display: none; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 30px; box-shadow: var(--shadow-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
                        <h3 style="font-size: 16px; margin: 0; color: var(--text-primary);">Standardized USPS Output</h3>
                        <button id="copy-standardized-btn" class="pill-btn active" style="padding: 8px 16px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: 12px; cursor: pointer;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
                            <span>Copy Formatted Address</span>
                        </button>
                    </div>
                    
                    <div id="standardized-address-output" style="background: var(--bg-tertiary); border: 1px border-color; border-radius: 6px; padding: 16px; font-family: monospace; font-size: 15px; font-weight: 700; color: var(--primary-color); white-space: pre-line; line-height: 1.6;"></div>
                    
                    <div style="margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 16px;">
                        <h4 style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 10px;">Applied Standardizations</h4>
                        <div id="applied-rules-list" style="display: flex; flex-wrap: wrap; gap: 8px;"></div>
                    </div>
                </div>

                <div class="faq-section" style="margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 30px;">
                    <h3 style="font-size: 18px; margin-bottom: 16px;">USPS Mailing Standards FAQ</h3>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">What is USPS Publication 28?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            USPS Publication 28 provides official guidelines for formatting addresses to optimize automated mail processing, sorting, and delivery speeds across the United States Postal Service network.
                        </p>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_std = PAGE_SEO['standardizer']
    _std_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/address-standardizer.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Format US addresses to USPS standards", "Uppercase city and state", "Standardize ZIP code format", "Copy formatted address"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_std_schema)}</script>',
                         keywords=_seo_std['keywords'], canonical_url="https://usa-address-zip.vercel.app/address-standardizer.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "address-standardizer.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated address-standardizer.html")

def generate_compare_page():
    print("Generating ZIP Code Compare page (compare.html)...")
    title = "ZIP Code Comparison Tool - Compare U.S. Postal Codes Side by Side"
    description = "Compare U.S. ZIP codes side-by-side. Inspect primary cities, state, county details, centroid coordinates, straight-line distance, and time zones."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">ZIP Compare</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">ZIP Code Side-by-Side Comparison</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Select up to 3 U.S. postal codes to compare geographic locations, counties, coordinate centroids, distances, and estimated time zones in a side-by-side matrix.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
                        <div style="position: relative;">
                            <label style="display: block; font-weight: 600; font-size: 13px; margin-bottom: 6px;">ZIP Code #1</label>
                            <input type="text" id="cmp-zip1" class="search-input" placeholder="Type 5-digit ZIP or City..." style="font-size: 14px; height: 40px;" autocomplete="off">
                            <div id="suggestions-cmp1" class="suggestions-box" style="top: 100%; max-height: 200px;"></div>
                        </div>
                        <div style="position: relative;">
                            <label style="display: block; font-weight: 600; font-size: 13px; margin-bottom: 6px;">ZIP Code #2</label>
                            <input type="text" id="cmp-zip2" class="search-input" placeholder="Type 5-digit ZIP or City..." style="font-size: 14px; height: 40px;" autocomplete="off">
                            <div id="suggestions-cmp2" class="suggestions-box" style="top: 100%; max-height: 200px;"></div>
                        </div>
                        <div style="position: relative;">
                            <label style="display: block; font-weight: 600; font-size: 13px; margin-bottom: 6px;">ZIP Code #3 (Optional)</label>
                            <input type="text" id="cmp-zip3" class="search-input" placeholder="Type 5-digit ZIP or City..." style="font-size: 14px; height: 40px;" autocomplete="off">
                            <div id="suggestions-cmp3" class="suggestions-box" style="top: 100%; max-height: 200px;"></div>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: flex-end;">
                        <button id="compare-btn" class="search-btn" style="padding: 10px 24px; font-size: 14px; display: inline-flex; align-items: center; gap: 8px; cursor: pointer;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                            <span>Compare ZIPs</span>
                        </button>
                    </div>
                </div>
                
                <div id="cmp-results-wrapper" style="display: none; margin-bottom: 30px; overflow-x: auto;">
                    <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); box-shadow: var(--shadow-sm); overflow: hidden;">
                        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                            <thead id="cmp-table-head"></thead>
                            <tbody id="cmp-table-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_compare = PAGE_SEO['compare']
    _compare_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/compare.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Compare two ZIP codes side-by-side", "View county, city, state details", "Calculate distance between compared ZIP codes", "Time zone comparison"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_compare_schema)}</script>',
                         keywords=_seo_compare['keywords'], canonical_url="https://usa-address-zip.vercel.app/compare.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "compare.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated compare.html")

def generate_timezone_page():
    print("Generating Time Zone Finder page (timezone.html)...")
    title = "Time Zone by ZIP Code Finder - U.S. Local Time Clocks"
    description = "Lookup U.S. time zones by ZIP code or city. Features live digital local clocks, UTC offsets, and state time zone boundaries."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Time Zone Finder</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">U.S. Time Zone & Live Local Clock Finder</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Enter any U.S. postal code or city to find its official U.S. Time Zone, current local clock time, UTC offset, and state location.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <div style="position: relative; max-width: 500px; margin: 0 auto;">
                        <label for="tz-origin" style="display: block; font-weight: 600; font-size: 14px; margin-bottom: 8px;">Enter ZIP Code or City</label>
                        <div class="search-bar-container" style="padding: 2px 2px 2px 12px; border: 1px solid var(--border-color); background: var(--bg-secondary);">
                            <input type="text" id="tz-origin" class="search-input" placeholder="e.g. 90210 or Beverly Hills..." autocomplete="off" style="font-size: 14px; height: 40px;">
                            <button id="tz-search-btn" class="search-btn" style="padding: 0 20px;">Find Time Zone</button>
                        </div>
                        <div id="suggestions-tz" class="suggestions-box" style="top: 100%; max-height: 200px;"></div>
                    </div>
                </div>
                
                <div id="tz-result-wrapper" style="display: none; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 28px; margin-bottom: 30px; text-align: center; box-shadow: var(--shadow-sm);">
                    <div id="tz-zone-badge" style="display: inline-block; background: var(--accent-gradient); color: #fff; padding: 6px 18px; border-radius: 20px; font-weight: 700; font-size: 14px; margin-bottom: 16px;"></div>
                    <div id="tz-clock-display" style="font-size: 44px; font-weight: 800; font-family: monospace; color: var(--primary-color); margin-bottom: 8px;"></div>
                    <div id="tz-details-sub" style="font-size: 15px; color: var(--text-secondary); font-weight: 500;"></div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_tz = PAGE_SEO['timezone']
    _tz_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/timezone.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Lookup time zone by ZIP code", "Live digital local clocks", "UTC offset display", "State time zone reference guide"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_tz_schema)}</script>',
                         keywords=_seo_tz['keywords'], canonical_url="https://usa-address-zip.vercel.app/timezone.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "timezone.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated timezone.html")

def generate_areacode_page():
    print("Generating Area Code Lookup page (area-codes.html)...")
    title = "Area Code to ZIP Code Lookup - U.S. Telephone Area Code Directory"
    description = "Look up any 3-digit U.S. phone area code. Find matching state, primary cities, counties, and associated postal codes."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Area Code Lookup</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">U.S. Phone Area Code Directory</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary);">
                    Search any 3-digit U.S. telephone area code to view the primary state, major cities, counties, and associated ZIP codes.
                </p>
                
                <div class="calculator-card" style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 24px;">
                    <div style="display: flex; gap: 12px; max-width: 450px; margin: 0 auto;">
                        <input type="text" id="ac-input" class="search-input" placeholder="Type 3-digit area code (e.g. 212, 310, 415)..." maxlength="3" style="font-size: 15px; height: 42px; text-align: center; font-weight: 700; letter-spacing: 2px;">
                        <button id="ac-search-btn" class="search-btn" style="padding: 0 24px;">Lookup Area Code</button>
                    </div>
                </div>
                
                <div id="ac-result-wrapper" style="display: none; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); padding: 24px; margin-bottom: 30px; box-shadow: var(--shadow-sm);">
                    <div id="ac-header-title" style="font-size: 20px; font-weight: 700; color: var(--primary-color); margin-bottom: 12px;"></div>
                    <div id="ac-details-body" style="font-size: 14px; color: var(--text-primary); line-height: 1.8;"></div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_ac = PAGE_SEO['area_codes']
    _ac_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/area-codes.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Lookup US phone area codes", "Find area code by ZIP code", "Complete US area code directory", "Filter by state"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_ac_schema)}</script>',
                         keywords=_seo_ac['keywords'], canonical_url="https://usa-address-zip.vercel.app/area-codes.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "area-codes.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated area-codes.html")

def generate_virtual_address_page():
    print("Generating Virtual US Address page (virtual-address.html)...")
    title = "Virtual US Address Directory & Mail Forwarding Guide"
    description = "Get a free or cheap virtual US address for business or personal package forwarding. Find recommended tax-free state ZIP codes for shopping and reshipping."
    
    breadcrumbs_list = '<li><a href="index.html">Home</a></li><li class="active">Virtual Address Guide</li>'
    breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
    
    body_content = """
    <div class="container animate-fade-in" style="margin-top: 30px;">
        <div class="detail-layout">
            <div class="main-content">
                <h2 class="section-title" style="margin-bottom: 24px;">Virtual U.S. Address & Mail Forwarding Directory</h2>
                <p style="margin-bottom: 24px; font-size: 15px; color: var(--text-secondary); line-height: 1.6;">
                    A <strong>Virtual U.S. Address</strong> allows international shoppers, business owners, and software developers to get a real street address in the United States. 
                    This guide details how U.S. package reshipping/proxy forwarding works and highlights the best states to get a virtual address to save on taxes.
                </p>
                
                <h3 style="font-size: 18px; margin: 28px 0 16px 0; color: var(--text-primary);">How U.S. Package Reshipping Works</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 18px;">
                        <div style="font-size: 24px; font-weight: 800; color: var(--primary-color); margin-bottom: 8px;">01</div>
                        <h4 style="font-size: 14px; margin-bottom: 6px;">Sign Up & Get Address</h4>
                        <p style="font-size: 12.5px; color: var(--text-secondary); margin: 0;">Register with a proxy shipping provider to get a unique U.S. street address with box number.</p>
                    </div>
                    <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 18px;">
                        <div style="font-size: 24px; font-weight: 800; color: var(--primary-color); margin-bottom: 8px;">02</div>
                        <h4 style="font-size: 14px; margin-bottom: 6px;">Shop U.S. Stores</h4>
                        <p style="font-size: 12.5px; color: var(--text-secondary); margin: 0;">Use your new U.S. address at checkout on sites like Amazon, eBay, or Walmart that restrict international postage.</p>
                    </div>
                    <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 6px; padding: 18px;">
                        <div style="font-size: 24px; font-weight: 800; color: var(--primary-color); margin-bottom: 8px;">03</div>
                        <h4 style="font-size: 14px; margin-bottom: 6px;">Reship to Your Country</h4>
                        <p style="font-size: 12.5px; color: var(--text-secondary); margin: 0;">The warehouse receives your packages, consolidates them to save on fees, and ships them to your home address.</p>
                    </div>
                </div>

                <h3 style="font-size: 18px; margin: 28px 0 16px 0; color: var(--text-primary);">Best Tax-Free U.S. States for Virtual Addresses</h3>
                <p style="margin-bottom: 16px; font-size: 14.5px; color: var(--text-secondary); line-height: 1.6;">
                    When choosing a U.S. reshipper address, selecting a state with <strong>0% Sales Tax</strong> will save you up to 10% on your online purchases. 
                    Below are the top states used by proxy shipping services:
                </p>

                <div style="overflow-x: auto; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--card-radius); margin-bottom: 30px; box-shadow: var(--shadow-sm);">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                        <thead>
                            <tr style="border-bottom: 2px solid var(--border-color); background: var(--bg-tertiary);">
                                <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">U.S. State</th>
                                <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 100px;">Sales Tax</th>
                                <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary); width: 110px;">Sample ZIP</th>
                                <th style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Proximity / Ideal Use</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid var(--border-color);">
                                <td style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Delaware (DE)</td>
                                <td style="padding: 12px 16px; color: var(--primary-color); font-weight: 700;">0%</td>
                                <td style="padding: 12px 16px; font-family: monospace;">19711 (Newark)</td>
                                <td style="padding: 12px 16px; color: var(--text-secondary);">East Coast. Excellent for transatlantic forwarding to Europe, UK, and Africa.</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border-color);">
                                <td style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Oregon (OR)</td>
                                <td style="padding: 12px 16px; color: var(--primary-color); font-weight: 700;">0%</td>
                                <td style="padding: 12px 16px; font-family: monospace;">97230 (Portland)</td>
                                <td style="padding: 12px 16px; color: var(--text-secondary);">West Coast. Best choice for shipping to Asia-Pacific, Japan, and Australia.</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border-color);">
                                <td style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">Montana (MT)</td>
                                <td style="padding: 12px 16px; color: var(--primary-color); font-weight: 700;">0%</td>
                                <td style="padding: 12px 16px; font-family: monospace;">59715 (Bozeman)</td>
                                <td style="padding: 12px 16px; color: var(--text-secondary);">Northern Border. Ideal for business entity setup or vehicle registration.</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border-color);">
                                <td style="padding: 12px 16px; font-weight: 600; color: var(--text-primary);">New Hampshire (NH)</td>
                                <td style="padding: 12px 16px; color: var(--primary-color); font-weight: 700;">0%</td>
                                <td style="padding: 12px 16px; font-family: monospace;">03060 (Nashua)</td>
                                <td style="padding: 12px 16px; color: var(--text-secondary);">New England. Popular alternative for Atlantic and Canadian freight.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="faq-section" style="margin-top: 40px; border-top: 1px solid var(--border-color); padding-top: 30px;">
                    <h3 style="font-size: 18px; margin-bottom: 16px;">Frequently Asked Questions</h3>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">Is it legal to use a virtual US address?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            Yes. Using a virtual U.S. address or package reshipping warehouse is completely legal. It is a standard service authorized by the USPS under form CMRA 1583 (Commercial Mail Receiving Agency guidelines).
                        </p>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">Can I use this address for commercial business registration?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            Yes. Many international entrepreneurs use virtual business addresses in states like Delaware or Wyoming to register LLCs, obtain EIN tax IDs, and run U.S.-based companies remotely.
                        </p>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; margin-bottom: 4px; color: var(--text-primary);">How do I get a free virtual US address?</h4>
                        <p style="font-size: 13.5px; color: var(--text-secondary);">
                            Many package reshippers offer free U.S. addresses with no monthly membership costs. You only pay for postage, parcel consolidation, and shipping fees when forwarding items to your home country.
                        </p>
                    </div>
                </div>
            </div>
            {SIDEBAR_HTML}
        </div>
    </div>
    """
    
    _seo_va = PAGE_SEO['virtual_address']
    _va_schema = {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": title, "description": description,
        "url": "https://usa-address-zip.vercel.app/virtual-address.html",
        "applicationCategory": "UtilitiesApplication", "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript. Requires HTML5.",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": ["Find tax-free US states for package forwarding", "Virtual US address guide", "Compare reshipping services", "No sales tax ZIP code directory"]
    }
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=f'<script type="application/ld+json">{json.dumps(_va_schema)}</script>',
                         keywords=_seo_va['keywords'], canonical_url="https://usa-address-zip.vercel.app/virtual-address.html", og_image=SITE_OG_IMAGE)
    html += breadcrumbs_html
    html += body_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    
    with open(os.path.join(DIST_DIR, "virtual-address.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Generated virtual-address.html")

# Main build execution
if __name__ == "__main__":
    generate_homepage()
    generate_state_pages()
    generate_county_pages()
    generate_info_pages()
    generate_distance_page()
    generate_address_generator_page()
    generate_radius_page()
    generate_standardizer_page()
    generate_compare_page()
    generate_timezone_page()
    generate_areacode_page()
    generate_virtual_address_page()
    print("All pages successfully built!")
