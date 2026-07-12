// global variables
let searchIndex = null;
let searchTimeout = null;

// Helper function to resolve root path dynamically based on URL path depth
function getRootPath() {
    const path = window.location.pathname;
    if (path.includes('/state/') || path.includes('/county/')) {
        return '../';
    }
    return '';
}

// Load Search Index on demand (when user focuses search input)
async function loadSearchIndex() {
    if (searchIndex) return;
    try {
        const root = getRootPath();
        const response = await fetch(`${root}data/search-index.json`);
        searchIndex = await response.json();
    } catch (e) {
        console.error("Failed to load search index", e);
    }
}

// Format slug (matches python builder make_slug)
function makeSlug(name) {
    return name.toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

// Setup Event Listeners when page loads
document.addEventListener("DOMContentLoaded", () => {
    // 0. Theme Toggle setup
    const themeToggleBtn = document.getElementById("theme-toggle");
    if (themeToggleBtn) {
        const sunIcon = themeToggleBtn.querySelector(".sun-icon");
        const moonIcon = themeToggleBtn.querySelector(".moon-icon");
        
        const currentTheme = localStorage.getItem("theme") || "light";
        if (currentTheme === "dark") {
            document.body.classList.add("dark-mode");
            if (sunIcon) sunIcon.style.display = "none";
            if (moonIcon) moonIcon.style.display = "inline-block";
        } else {
            document.body.classList.remove("dark-mode");
            if (sunIcon) sunIcon.style.display = "inline-block";
            if (moonIcon) moonIcon.style.display = "none";
        }
        
        themeToggleBtn.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
            const isDark = document.body.classList.contains("dark-mode");
            localStorage.setItem("theme", isDark ? "dark" : "light");
            
            if (isDark) {
                if (sunIcon) sunIcon.style.display = "none";
                if (moonIcon) moonIcon.style.display = "inline-block";
            } else {
                if (sunIcon) sunIcon.style.display = "inline-block";
                if (moonIcon) moonIcon.style.display = "none";
            }
        });
    }

    // 1. Setup Global Autocomplete Search
    const searchInput = document.getElementById("global-search");
    const suggestionsBox = document.getElementById("suggestions");
    const clearBtn = document.getElementById("clear-search");
    const searchActionBtn = document.getElementById("search-action-btn");
    
    if (searchInput) {
        // Preload search index on hover or focus to keep UI snappy
        searchInput.addEventListener("focus", loadSearchIndex);
        searchInput.addEventListener("mouseenter", loadSearchIndex);

        searchInput.addEventListener("input", () => {
            const query = searchInput.value.trim().toLowerCase();
            
            if (query.length > 0) {
                if (clearBtn) clearBtn.style.display = "flex";
            } else {
                if (clearBtn) clearBtn.style.display = "none";
                if (suggestionsBox) suggestionsBox.style.display = "none";
                return;
            }
            
            // Debounce search
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                showSuggestions(query);
            }, 100);
        });

        // Hide suggestions when clicking outside
        document.addEventListener("click", (e) => {
            if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
                suggestionsBox.style.display = "none";
            }
        });

        // Keyboard Shortcut: press "/" to focus search
        document.addEventListener("keydown", (e) => {
            if (e.key === "/" && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
            
            // Escape to close suggestions
            if (e.key === "Escape" && suggestionsBox) {
                suggestionsBox.style.display = "none";
            }
        });

        if (clearBtn) {
            clearBtn.addEventListener("click", () => {
                searchInput.value = "";
                clearBtn.style.display = "none";
                suggestionsBox.style.display = "none";
                searchInput.focus();
            });
        }
        
        if (searchActionBtn) {
            searchActionBtn.addEventListener("click", () => {
                const query = searchInput.value.trim();
                if (query.length > 0) {
                    // Try to direct match or trigger first item
                    const activeItem = suggestionsBox.querySelector(".suggestion-item");
                    if (activeItem) {
                        activeItem.click();
                    }
                }
            });
        }
    }

    // 2. Setup State Counties Filter
    const countyFilter = document.getElementById("county-filter");
    if (countyFilter) {
        const countyList = document.getElementById("county-list");
        const countyCards = countyList.getElementsByClassName("list-item-card");
        
        countyFilter.addEventListener("input", () => {
            const q = countyFilter.value.trim().toLowerCase();
            for (let card of countyCards) {
                const name = card.getAttribute("data-name");
                if (name.includes(q)) {
                    card.style.display = "flex";
                } else {
                    card.style.display = "none";
                }
            }
        });
    }

    // 3. Setup County Cities Filter
    const cityFilter = document.getElementById("city-filter");
    if (cityFilter) {
        const sectionsContainer = document.getElementById("zip-sections-container");
        const citySections = sectionsContainer.getElementsByClassName("city-section");
        
        cityFilter.addEventListener("input", () => {
            const q = cityFilter.value.trim().toLowerCase();
            for (let sec of citySections) {
                const name = sec.getAttribute("data-city");
                if (name.includes(q)) {
                    sec.style.display = "block";
                } else {
                    sec.style.display = "none";
                }
            }
        });
    }

    // 4. Check for ZIP scroll parameters on load
    handleIncomingZipHighlight();

    // 5. Geolocation Search Setup
    const geoBtn = document.getElementById("geo-search-btn");
    if (geoBtn) {
        geoBtn.addEventListener("click", async () => {
            const originalText = geoBtn.innerHTML;
            geoBtn.disabled = true;
            geoBtn.innerHTML = `
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="vertical-align: middle; margin-right: 4px; animation: spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25"></circle><path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span>Locating...</span>
            `;
            
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    try {
                        geoBtn.innerHTML = `<span>Searching ZIP...</span>`;
                        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                        const data = await res.json();
                        
                        if (data && data.address) {
                            const zipcode = data.address.postcode;
                            if (zipcode) {
                                await loadSearchIndex();
                                if (searchIndex && searchIndex.zips[zipcode]) {
                                    const details = searchIndex.zips[zipcode];
                                    const stateAbbr = details[0];
                                    const county = details[1];
                                    const countySlug = makeSlug(county);
                                    const countyKey = `${stateAbbr.toLowerCase()}-${countySlug}`;
                                    
                                    showToast(`Located: ${data.address.city || ''} (${zipcode})`);
                                    setTimeout(() => {
                                        window.location.href = `${getRootPath()}county/${countyKey}.html?zip=${zipcode}`;
                                    }, 1200);
                                } else {
                                    showToast(`ZIP ${zipcode} found. Redirecting...`);
                                    const mainSearchInput = document.getElementById("global-search");
                                    if (mainSearchInput) {
                                        mainSearchInput.value = zipcode;
                                        showSuggestions(zipcode);
                                    }
                                    geoBtn.innerHTML = originalText;
                                    geoBtn.disabled = false;
                                }
                            } else {
                                showToast("Could not find ZIP code at location.");
                                geoBtn.innerHTML = originalText;
                                geoBtn.disabled = false;
                            }
                        } else {
                            showToast("Address lookup failed.");
                            geoBtn.innerHTML = originalText;
                            geoBtn.disabled = false;
                        }
                    } catch (err) {
                        console.error(err);
                        showToast("Failed to fetch location data.");
                        geoBtn.innerHTML = originalText;
                        geoBtn.disabled = false;
                    }
                },
                (error) => {
                    console.warn(error);
                    showToast("Location access denied or unavailable.");
                    geoBtn.innerHTML = originalText;
                    geoBtn.disabled = false;
                },
                { timeout: 8000 }
            );
        });
    }
});

// Perform Autocomplete Match
function showSuggestions(query) {
    if (!searchIndex) return;
    const suggestionsBox = document.getElementById("suggestions");
    if (!suggestionsBox) return;

    const matches = [];
    const maxSuggestions = 10;
    const root = getRootPath();

    // Clean query
    const cleanQuery = query.trim().toLowerCase();

    // A. Match States
    for (let s of searchIndex.states) {
        if (s.n.toLowerCase().includes(cleanQuery) || s.a.toLowerCase() === cleanQuery) {
            matches.push({
                type: 'state',
                title: s.n,
                subtitle: `United States Area (${s.a})`,
                badge: 'State',
                url: `${root}state/${s.s}.html`
            });
        }
    }

    // B. Match Counties
    for (let c of searchIndex.counties) {
        if (matches.length >= maxSuggestions) break;
        if (c.n.toLowerCase().includes(cleanQuery)) {
            matches.push({
                type: 'county',
                title: `${c.n} County`,
                subtitle: `${c.st}, ${c.a}`,
                badge: 'County',
                url: `${root}county/${c.s}.html`
            });
        }
    }

    // C. Match Cities and ZIPs in dictionary
    // If query looks like a zip (numeric)
    const isNumeric = /^\d+$/.test(cleanQuery);
    
    let zipMatchCount = 0;
    for (let [zip, details] of Object.entries(searchIndex.zips)) {
        if (matches.length >= maxSuggestions) break;
        if (zipMatchCount >= 5) break; // Limit zip results so they don't drown states/counties
        
        const [stateAbbr, county, city] = details;
        
        const zipMatches = zip.startsWith(cleanQuery);
        const cityMatches = !isNumeric && city.toLowerCase().includes(cleanQuery);

        if (zipMatches || cityMatches) {
            const countySlug = makeSlug(county);
            const countyKey = `${stateAbbr.toLowerCase()}-${countySlug}`;
            
            matches.push({
                type: 'zip',
                title: `${zip} - ${city}`,
                subtitle: `${county} County, ${stateAbbr}`,
                badge: 'ZIP Code',
                url: `${root}county/${countyKey}.html?zip=${zip}`,
                zip: zip
            });
            zipMatchCount++;
        }
    }

    // Render Suggestions
    if (matches.length === 0) {
        suggestionsBox.innerHTML = `
            <div style="padding: 16px 20px; font-size: 14px; color: var(--text-muted); text-align: center;">
                No results found for "<strong>${escapeHtml(query)}</strong>"
            </div>
        `;
    } else {
        let itemsHtml = "";
        matches.slice(0, maxSuggestions).forEach((item, idx) => {
            const icon = item.type === 'state' ? '🗺️' : (item.type === 'county' ? '📍' : '✉️');
            itemsHtml += `
            <div class="suggestion-item ${idx === 0 ? 'active' : ''}" onclick="window.location.href='${item.url}'">
                <div class="suggestion-left">
                    <div class="suggestion-icon">${icon}</div>
                    <div>
                        <div class="suggestion-title">${highlightMatch(item.title, query)}</div>
                        <div class="suggestion-subtitle">${item.subtitle}</div>
                    </div>
                </div>
                <span class="suggestion-badge">${item.badge}</span>
            </div>
            `;
        });
        suggestionsBox.innerHTML = itemsHtml;
    }
    
    suggestionsBox.style.display = "block";
}

// Highlight query matches in autocomplete
function highlightMatch(text, query) {
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return text;
    const len = query.length;
    return text.substring(0, idx) + 
           `<span class="highlight">${text.substring(idx, idx + len)}</span>` + 
           text.substring(idx + len);
}

// Escape HTML entities to prevent injection in template
function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// Copy ZIP Code function
function copyZipCode(zipCode) {
    navigator.clipboard.writeText(zipCode).then(() => {
        showToast(`ZIP Code ${zipCode} copied to clipboard!`);
    }).catch(err => {
        console.error('Could not copy text: ', err);
    });
}

// Show beautiful notification toast
function showToast(message) {
    const toast = document.getElementById("copy-toast");
    const toastMsg = document.getElementById("toast-message");
    if (!toast || !toastMsg) return;
    
    toastMsg.textContent = message;
    toast.classList.add("show");
    
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2200);
}

// Highlight ZIP code on county page if passed in query string
function handleIncomingZipHighlight() {
    const params = new URLSearchParams(window.location.search);
    const targetZip = params.get("zip");
    if (!targetZip) return;
    
    // Find ZIP card on page
    setTimeout(() => {
        const cards = document.getElementsByClassName("zip-card");
        for (let card of cards) {
            const zipTextEl = card.querySelector(".zip-code-text");
            if (zipTextEl && zipTextEl.textContent.trim() === targetZip) {
                // Focus styling
                card.style.borderColor = "var(--primary-color)";
                card.style.background = "var(--bg-secondary)";
                card.style.boxShadow = "var(--shadow-glow)";
                
                // Scroll into view nicely
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Pulse animation
                card.style.transform = "scale(1.08)";
                setTimeout(() => {
                    card.style.transform = "scale(1)";
                }, 800);
                break;
            }
        }
    }, 200);
}

// Pill click filter handler
window.filterByPill = function(citySlug, btn) {
    const container = btn.parentElement;
    const buttons = container.getElementsByClassName("pill-btn");
    for (let button of buttons) {
        button.classList.remove("active");
    }
    btn.classList.add("active");
    
    const sectionsContainer = document.getElementById("zip-sections-container");
    if (!sectionsContainer) return;
    const citySections = sectionsContainer.getElementsByClassName("city-section");
    
    for (let sec of citySections) {
        const slug = sec.getAttribute("data-city-slug");
        if (citySlug === 'all' || slug === citySlug) {
            sec.style.display = "block";
        } else {
            sec.style.display = "none";
        }
    }
};
