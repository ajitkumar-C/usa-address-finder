import os
import csv
import json
import urllib.request
import re

# Constants
CSV_URL = "https://raw.githubusercontent.com/scpike/us-state-county-zip/master/geo-data.csv"
CSV_FILE = "geo-data.csv"
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
        zip_index[zipcode] = [abbr, county, city]
        
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

# HTML Base Template Components
HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="stylesheet" href="{root_path}css/style.css">
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
            <nav style="display: flex; align-items: center; gap: 16px;">
                <ul class="nav-links">
                    <li><a href="{root_path}index.html">Home</a></li>
                    <li><a href="{root_path}about.html">About</a></li>
                    <li><a href="{root_path}contact.html">Contact</a></li>
                </ul>
                <button id="theme-toggle" class="theme-toggle-btn" title="Toggle Light/Dark Mode">
                    <!-- Sun Icon -->
                    <svg class="sun-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
                    <!-- Moon Icon -->
                    <svg class="moon-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display: none;"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
                </button>
            </nav>
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
                        <li><a href="{root_path}sitemap.xml">XML Sitemap</a></li>
                        <li><a href="https://github.com/scpike/us-state-county-zip" target="_blank" rel="noopener">Data Source</a></li>
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

    <script src="{root_path}js/search.js"></script>
</body>
</html>
"""

# -----------------
# 1. GENERATE HOMEPAGE (index.html)
# -----------------
def generate_homepage():
    title = "USA Address Finder - Search ZIP Codes, Counties, & States"
    description = "Search all US postal codes, states, and counties. Quickly find zip codes in any state or sub-area with our instant visual autocomplete search engine."
    
    schema_data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "USA Address Finder",
        "url": "https://usa-address-zip.vercel.app/",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": "https://usa-address-zip.vercel.app/index.html?q={search_term_string}"
            },
            "query-input": "required name=search_term_string"
        }
    }
    schema_markup = f'<script type="application/ld+json">{json.dumps(schema_data)}</script>'
    
    # State Grid Items HTML
    state_items_html = ""
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

    # Assemble Homepage Body
    body_content = f"""
    <main class="hero animate-fade-in">
        <div class="container">
            <h1>Search <span>USA Address Finder</span></h1>
            <p>Instant visual lookup of all ZIP codes, counties, cities, and states. Enter a ZIP code, city, county, or state below to begin.</p>
            
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

        <h2 class="section-title">Explore by State</h2>
        <div class="states-grid">
            {state_items_html}
        </div>
    </div>
    """
    
    html = HEADER.format(title=title, description=description, root_path="", schema_markup=schema_markup)
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
        title = f"ZIP Codes in {state_name} - List of Counties & Areas ({data['abbr']})"
        description = f"Browse the full list of ZIP codes, counties, and cities in {state_name} ({data['abbr']}). Select a county to see specific postal codes."
        
        breadcrumbs_list = f'<li><a href="../index.html">Home</a></li><li class="active">{state_name}</li>'
        breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
        
        schema_data = {
            "@context": "https://schema.org",
            "@type": "AdministrativeArea",
            "name": state_name,
            "alternateName": data['abbr'],
            "description": f"State of {state_name} with {len(data['counties'])} counties and {data['total_zips']} zip codes.",
            "identifier": data['fips']
        }
        schema_markup = f'<script type="application/ld+json">{json.dumps(schema_data)}</script>'

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
                            <h2>{state_name}</h2>
                        </div>
                        <span style="font-size: 14px; color: var(--text-muted); font-weight: 600;">FIPS Code: {data['fips']}</span>
                    </div>

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

                    <div class="filter-box">
                        <h3 style="font-size: 16px; margin-bottom: 8px;">Filter Counties</h3>
                        <input type="text" id="county-filter" class="filter-input" placeholder="Type county name to filter...">
                    </div>

                    <div class="list-group" id="county-list">
                        {county_items_html}
                    </div>
                </div>
                {SIDEBAR_HTML}
            </div>
        </div>
        """
        
        html = HEADER.format(title=title, description=description, root_path="../", schema_markup=schema_markup)
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
            title = f"{county_name} County ZIP Codes, Cities, & Zones - {state_data['abbr']}"
            description = f"Detailed list of all ZIP codes and cities in {county_name} County, {state_name} ({state_data['abbr']}). Click to copy zip codes instantly."
            
            breadcrumbs_list = f'<li><a href="../index.html">Home</a></li><li><a href="../state/{state_data["slug"]}.html">{state_name}</a></li><li class="active">{county_name} County</li>'
            breadcrumbs_html = BREADCRUMBS_HTML.format(breadcrumbs=breadcrumbs_list)
            
            schema_data = {
                "@context": "https://schema.org",
                "@type": "AdministrativeArea",
                "name": f"{county_name} County",
                "containedInPlace": {
                    "@type": "AdministrativeArea",
                    "name": state_name
                },
                "description": f"County of {county_name} located in {state_name} with {county_data['total_zips']} zip codes."
            }
            schema_markup = f'<script type="application/ld+json">{json.dumps(schema_data)}</script>'

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

                        <div class="filter-box">
                            <h3 style="font-size: 16px; margin-bottom: 8px;">Filter by City</h3>
                            <input type="text" id="city-filter" class="filter-input" placeholder="Type city name to filter ZIP codes...">
                            {city_pills_html}
                        </div>

                        <div id="zip-sections-container">
                            {zips_by_city_html}
                        </div>
                    </div>
                    {SIDEBAR_HTML}
                </div>
            </div>
            """
            
            html = HEADER.format(title=title, description=description, root_path="../", schema_markup=schema_markup)
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
    html = HEADER.format(title=about_title, description=about_desc, root_path="", schema_markup="")
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
    html = HEADER.format(title=contact_title, description=contact_desc, root_path="", schema_markup="")
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
    html = HEADER.format(title=privacy_title, description=privacy_desc, root_path="", schema_markup="")
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
    html = HEADER.format(title=disc_title, description=disc_desc, root_path="", schema_markup="")
    html += disc_content.format(SIDEBAR_HTML=SIDEBAR_HTML)
    html += FOOTER.format(root_path="")
    with open(os.path.join(DIST_DIR, "disclaimer.html"), "w", encoding="utf-8") as f:
        f.write(html)
        
    print("All info pages generated successfully.")

# Main build execution
if __name__ == "__main__":
    generate_homepage()
    generate_state_pages()
    generate_county_pages()
    generate_info_pages()
    print("All pages successfully built!")
