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

    // 0.b Responsive Navigation Toggle Setup
    const menuToggleBtn = document.getElementById("menu-toggle");
    const menuCloseBtn = document.getElementById("menu-close");
    const navLinks = document.querySelector(".nav-links");
    const navOverlay = document.getElementById("nav-overlay");
    
    if (menuToggleBtn && navLinks && navOverlay) {
        const openMenu = () => {
            navLinks.classList.add("open");
            navOverlay.classList.add("show");
            document.body.style.overflow = "hidden";
        };
        
        const closeMenu = () => {
            navLinks.classList.remove("open");
            navOverlay.classList.remove("show");
            document.body.style.overflow = "";
        };
        
        menuToggleBtn.addEventListener("click", openMenu);
        if (menuCloseBtn) {
            menuCloseBtn.addEventListener("click", closeMenu);
        }
        navOverlay.addEventListener("click", closeMenu);
        
        const links = navLinks.querySelectorAll("a");
        for (let link of links) {
            link.addEventListener("click", closeMenu);
        }
        
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && navLinks.classList.contains("open")) {
                closeMenu();
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

    // 6. Setup Distance Calculator (if elements exist)
    const zip1Input = document.getElementById("zip1");
    const zip2Input = document.getElementById("zip2");
    if (zip1Input && zip2Input) {
        setupCalcAutocomplete("zip1", "suggestions-zip1");
        setupCalcAutocomplete("zip2", "suggestions-zip2");

        const calcBtn = document.getElementById("calculate-btn");
        if (calcBtn) {
            calcBtn.addEventListener("click", () => {
                performDistanceCalculation(zip1Input.value.trim(), zip2Input.value.trim());
            });
        }

        // Support Enter key triggers
        const handleEnter = (e) => {
            if (e.key === "Enter") {
                performDistanceCalculation(zip1Input.value.trim(), zip2Input.value.trim());
            }
        };
        zip1Input.addEventListener("keydown", handleEnter);
        zip2Input.addEventListener("keydown", handleEnter);

        // Share copy link button
        const copyShareBtn = document.getElementById("copy-share-btn");
        if (copyShareBtn) {
            copyShareBtn.addEventListener("click", () => {
                const shareUrlInput = document.getElementById("share-url");
                if (shareUrlInput && shareUrlInput.value) {
                    navigator.clipboard.writeText(shareUrlInput.value).then(() => {
                        showToast("Shareable link copied to clipboard!");
                    }).catch(err => {
                        console.error("Failed to copy link:", err);
                    });
                }
            });
        }

        // Check for URL params
        const params = new URLSearchParams(window.location.search);
        const paramZip1 = params.get("zip1");
        const paramZip2 = params.get("zip2");
        if (paramZip1 && paramZip2) {
            zip1Input.value = paramZip1;
            zip2Input.value = paramZip2;

            const clear1 = document.getElementById("clear-zip1");
            const clear2 = document.getElementById("clear-zip2");
            if (clear1) clear1.style.display = "flex";
            if (clear2) clear2.style.display = "flex";

            loadSearchIndex().then(() => {
                performDistanceCalculation(paramZip1, paramZip2);
            });
        }
    }

    // 7. Setup Address Generator (if elements exist)
    const genInput = document.getElementById("gen-search");
    if (genInput) {
        setupGenAutocomplete("gen-search", "suggestions-gen");
        
        const generateBtn = document.getElementById("generate-btn");
        if (generateBtn) {
            generateBtn.addEventListener("click", () => {
                triggerAddressGeneration();
            });
        }
        
        // Clear generator search button
        const clearGenBtn = document.getElementById("clear-gen");
        if (clearGenBtn) {
            clearGenBtn.addEventListener("click", () => {
                genInput.value = "";
                clearGenBtn.style.display = "none";
                document.getElementById("suggestions-gen").style.display = "none";
                genInput.focus();
                
                // Reset scope globally to all
                window.generatorScope = { type: 'all' };
                document.getElementById("active-scope").querySelector("span strong").textContent = "United States (All)";
                document.getElementById("share-container").style.display = "none";
                triggerAddressGeneration();
            });
        }
        
        // Share copy link button
        const copyShareBtn = document.getElementById("gen-copy-share-btn");
        if (copyShareBtn) {
            copyShareBtn.addEventListener("click", () => {
                const shareUrlInput = document.getElementById("gen-share-url");
                if (shareUrlInput && shareUrlInput.value) {
                    navigator.clipboard.writeText(shareUrlInput.value).then(() => {
                        showToast("Shareable link copied to clipboard!");
                    }).catch(err => {
                        console.error("Failed to copy link:", err);
                    });
                }
            });
        }
        
        // Check for URL parameters to pre-fill scope
        const params = new URLSearchParams(window.location.search);
        const pState = params.get("state");
        const pCounty = params.get("county");
        const pCity = params.get("city");
        const pZip = params.get("zip");
        
        loadSearchIndex().then(() => {
            window.generatorScope = { type: 'all' };
            
            if (pZip) {
                const details = searchIndex.zips[pZip];
                if (details) {
                    genInput.value = pZip;
                    if (clearGenBtn) clearGenBtn.style.display = "flex";
                    window.generatorScope = { type: 'zip', code: pZip, city: details[2], state: details[0] };
                    document.getElementById("active-scope").querySelector("span strong").textContent = `ZIP Code: ${pZip} (${details[2]}, ${details[0]})`;
                }
            } else if (pState) {
                const stateObj = searchIndex.states.find(s => s.a.toLowerCase() === pState.toLowerCase() || s.n.toLowerCase() === pState.toLowerCase());
                if (stateObj) {
                    genInput.value = stateObj.n;
                    if (clearGenBtn) clearGenBtn.style.display = "flex";
                    window.generatorScope = { type: 'state', name: stateObj.n, code: stateObj.a };
                    document.getElementById("active-scope").querySelector("span strong").textContent = `State: ${stateObj.n}`;
                }
            } else if (pCounty) {
                const countyObj = searchIndex.counties.find(c => c.s.toLowerCase() === pCounty.toLowerCase() || c.n.toLowerCase() === pCounty.toLowerCase());
                if (countyObj) {
                    genInput.value = `${countyObj.n} County, ${countyObj.a}`;
                    if (clearGenBtn) clearGenBtn.style.display = "flex";
                    window.generatorScope = { type: 'county', name: countyObj.n, state: countyObj.a, key: countyObj.s };
                    document.getElementById("active-scope").querySelector("span strong").textContent = `County: ${countyObj.n} (${countyObj.a})`;
                }
            } else if (pCity) {
                let foundCity = null;
                let foundState = null;
                for (let [zip, details] of Object.entries(searchIndex.zips)) {
                    if (details[2].toLowerCase() === pCity.toLowerCase()) {
                        foundCity = details[2];
                        foundState = details[0];
                        break;
                    }
                }
                if (foundCity) {
                    genInput.value = `${foundCity}, ${foundState}`;
                    if (clearGenBtn) clearGenBtn.style.display = "flex";
                    window.generatorScope = { type: 'city', name: foundCity, state: foundState };
                    document.getElementById("active-scope").querySelector("span strong").textContent = `City: ${foundCity}, ${foundState}`;
                }
            }
            
            // Trigger initial generation
            triggerAddressGeneration();
        });
    }

    // 8. Setup Radius Finder (if elements exist)
    const radiusInput = document.getElementById("radius-origin");
    if (radiusInput) {
        setupRadiusAutocomplete("radius-origin", "suggestions-radius");
        
        const findZipsBtn = document.getElementById("find-zips-btn");
        if (findZipsBtn) {
            findZipsBtn.addEventListener("click", () => {
                triggerRadiusSearch();
            });
        }
        
        radiusInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                triggerRadiusSearch();
            }
        });
        
        const clearRadiusBtn = document.getElementById("clear-radius");
        if (clearRadiusBtn) {
            clearRadiusBtn.addEventListener("click", () => {
                radiusInput.value = "";
                clearRadiusBtn.style.display = "none";
                document.getElementById("suggestions-radius").style.display = "none";
                radiusInput.focus();
                window.radiusOriginScope = null;
                document.getElementById("radius-results-wrapper").style.display = "none";
            });
        }
        
        const radiusExportBtn = document.getElementById("radius-export-btn");
        if (radiusExportBtn) {
            radiusExportBtn.addEventListener("click", () => {
                if (window.lastRadiusResults && window.lastRadiusResults.length > 0) {
                    const headers = ["Distance (Miles)", "ZIP Code", "City", "State", "County", "Latitude", "Longitude"];
                    const rows = window.lastRadiusResults.map(item => [
                        item.distance.toFixed(2),
                        item.zip,
                        item.city,
                        item.state,
                        item.county,
                        item.lat || "",
                        item.lon || ""
                    ]);
                    const originName = window.radiusOriginScope ? window.radiusOriginScope.code || window.radiusOriginScope.name : radiusInput.value.replace(/ /g, "_");
                    const filename = `ZIP_Codes_Within_${document.getElementById("radius-range").value}_Miles_of_${originName}.csv`;
                    downloadListAsCSV(filename, headers, rows);
                }
            });
        }
    }
    
    // 9. Setup GPS Geolocation ("Find ZIP Codes Near Me") Button
    const findNearMeBtn = document.getElementById("find-near-me");
    if (findNearMeBtn) {
        findNearMeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            findNearMe();
        });
    }
    
    // 10. Setup State and County CSV Download Buttons
    document.addEventListener("click", (e) => {
        const stateBtn = e.target.closest(".state-csv-btn");
        if (stateBtn) {
            e.preventDefault();
            const stateAbbr = stateBtn.getAttribute("data-state-abbr");
            const stateName = stateBtn.getAttribute("data-state-name");
            loadSearchIndex().then(() => {
                const rows = [];
                for (let [zip, details] of Object.entries(searchIndex.zips)) {
                    const [abbr, county, city, lat, lon] = details;
                    if (abbr.toLowerCase() === stateAbbr.toLowerCase()) {
                        rows.push([zip, city, county, abbr, lat || "", lon || ""]);
                    }
                }
                rows.sort((a, b) => a[0].localeCompare(b[0]));
                downloadListAsCSV(`ZIP_Codes_${stateName.replace(/ /g, "_")}.csv`, ["ZIP Code", "City", "County", "State", "Latitude", "Longitude"], rows);
            });
            return;
        }
        
        const countyBtn = e.target.closest(".county-csv-btn");
        if (countyBtn) {
            e.preventDefault();
            const stateAbbr = countyBtn.getAttribute("data-state-abbr");
            const countyName = countyBtn.getAttribute("data-county-name");
            loadSearchIndex().then(() => {
                const rows = [];
                for (let [zip, details] of Object.entries(searchIndex.zips)) {
                    const [abbr, county, city, lat, lon] = details;
                    if (abbr.toLowerCase() === stateAbbr.toLowerCase() && county.toLowerCase() === countyName.toLowerCase()) {
                        rows.push([zip, city, county, abbr, lat || "", lon || ""]);
                    }
                }
                rows.sort((a, b) => a[0].localeCompare(b[0]));
                downloadListAsCSV(`ZIP_Codes_${countyName.replace(/ /g, "_")}_County_${stateAbbr}.csv`, ["ZIP Code", "City", "County", "State", "Latitude", "Longitude"], rows);
            });
            return;
        }
    });
    
    // 11. Setup Interactive US State Explorer Map Widget
    initUSStateMap();
    
    // 12. Setup USPS Address Standardizer
    initAddressStandardizer();
    
    // 13. Setup ZIP Code Compare Tool
    initZipCompare();
    
    // 14. Setup Time Zone Finder
    initTimeZoneFinder();
    
    // 15. Setup Area Code Directory Lookup
    initAreaCodeLookup();
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

// Distance Calculator Autocomplete Setup
function setupCalcAutocomplete(inputId, suggestionsId) {
    const input = document.getElementById(inputId);
    const suggestionsBox = document.getElementById(suggestionsId);
    const clearBtn = document.getElementById("clear-" + inputId);
    
    if (!input || !suggestionsBox) return;
    
    input.addEventListener("focus", loadSearchIndex);
    input.addEventListener("mouseenter", loadSearchIndex);
    
    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        
        if (query.length > 0) {
            if (clearBtn) clearBtn.style.display = "flex";
        } else {
            if (clearBtn) clearBtn.style.display = "none";
            suggestionsBox.style.display = "none";
            return;
        }
        
        if (!searchIndex) return;
        
        const matches = [];
        const maxSuggestions = 10;
        const isNumeric = /^\d+$/.test(query);
        
        for (let [zip, details] of Object.entries(searchIndex.zips)) {
            if (matches.length >= maxSuggestions) break;
            
            const [stateAbbr, county, city, lat, lon] = details;
            
            const zipMatches = zip.startsWith(query);
            const cityMatches = !isNumeric && city.toLowerCase().includes(query);
            
            if (zipMatches || cityMatches) {
                matches.push({
                    zip: zip,
                    city: city,
                    county: county,
                    stateAbbr: stateAbbr,
                    lat: lat,
                    lon: lon
                });
            }
        }
        
        if (matches.length === 0) {
            suggestionsBox.innerHTML = `
                <div style="padding: 12px 16px; font-size: 13px; color: var(--text-muted); text-align: center;">
                    No ZIP codes found
                </div>
            `;
        } else {
            let html = "";
            matches.forEach((item, idx) => {
                html += `
                <div class="suggestion-item" style="padding: 10px 16px; cursor: pointer; border-bottom: 1px solid var(--border-color); display: flex; flex-direction: column;" data-zip="${item.zip}">
                    <div style="font-weight: 600; color: var(--text-primary); font-size: 13px;">${item.zip} - ${item.city}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${item.county} County, ${item.stateAbbr}</div>
                </div>
                `;
            });
            suggestionsBox.innerHTML = html;
            
            // Add click event to each suggestion
            const items = suggestionsBox.getElementsByClassName("suggestion-item");
            for (let item of items) {
                item.addEventListener("click", () => {
                    const selectedZip = item.getAttribute("data-zip");
                    input.value = selectedZip;
                    suggestionsBox.style.display = "none";
                    if (clearBtn) clearBtn.style.display = "flex";
                });
            }
        }
        suggestionsBox.style.display = "block";
    });
    
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            input.value = "";
            clearBtn.style.display = "none";
            suggestionsBox.style.display = "none";
            input.focus();
        });
    }
    
    // Hide suggestions when clicking outside
    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = "none";
        }
    });
}

// Haversine Distance Formula
function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
    const R_MILES = 3958.8; // Earth's radius in miles
    const R_KM = 6371.0;    // Earth's radius in kilometers
    
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
        
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    
    return {
        miles: R_MILES * c,
        km: R_KM * c
    };
}

// Perform Distance Calculation
async function performDistanceCalculation(zip1, zip2) {
    const errorMsg = document.getElementById("error-message");
    const resultContainer = document.getElementById("result-container");
    
    if (!errorMsg || !resultContainer) return;
    
    errorMsg.style.display = "none";
    resultContainer.style.display = "none";
    
    if (!zip1 || !zip2) {
        showError("Please enter both ZIP codes.");
        return;
    }
    
    await loadSearchIndex();
    
    if (!searchIndex || !searchIndex.zips) {
        showError("Failed to load ZIP database. Please reload and try again.");
        return;
    }
    
    const details1 = searchIndex.zips[zip1];
    const details2 = searchIndex.zips[zip2];
    
    if (!details1) {
        showError(`Origin ZIP code "${zip1}" was not found.`);
        return;
    }
    
    if (!details2) {
        showError(`Destination ZIP code "${zip2}" was not found.`);
        return;
    }
    
    const [stateAbbr1, county1, city1, lat1, lon1] = details1;
    const [stateAbbr2, county2, city2, lat2, lon2] = details2;
    
    if (lat1 === null || lon1 === null || lat1 === undefined || lon1 === undefined) {
        showError(`Geographic coordinates are not available for ZIP code "${zip1}".`);
        return;
    }
    
    if (lat2 === null || lon2 === null || lat2 === undefined || lon2 === undefined) {
        showError(`Geographic coordinates are not available for ZIP code "${zip2}".`);
        return;
    }
    
    if (zip1 === zip2) {
        showError("Origin and destination ZIP codes must be different.");
        return;
    }
    
    const dist = calculateHaversineDistance(lat1, lon1, lat2, lon2);
    
    // Set text outputs
    document.getElementById("dist-miles").textContent = dist.miles.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    document.getElementById("dist-km").textContent = dist.km.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    document.getElementById("zip1-title").textContent = zip1;
    document.getElementById("zip1-detail").textContent = `${city1}, ${county1} County, ${stateAbbr1}`;
    document.getElementById("zip1-lat").textContent = lat1.toFixed(4);
    document.getElementById("zip1-lon").textContent = lon1.toFixed(4);
    
    document.getElementById("zip2-title").textContent = zip2;
    document.getElementById("zip2-detail").textContent = `${city2}, ${county2} County, ${stateAbbr2}`;
    document.getElementById("zip2-lat").textContent = lat2.toFixed(4);
    document.getElementById("zip2-lon").textContent = lon2.toFixed(4);
    
    document.getElementById("svg-zip1").textContent = zip1;
    document.getElementById("svg-zip2").textContent = zip2;
    
    // Update SVG arc line path based on distance to add subtle curve styling
    const arcEl = document.getElementById("svg-arc");
    if (arcEl) {
        // Curve strength based on distance, but capped
        const distFactor = Math.min(dist.miles / 20, 45);
        const controlY = 30 - distFactor;
        arcEl.setAttribute("d", `M 40 30 Q 200 ${controlY} 360 30`);
    }
    
    // Update sharing URL input
    const shareUrlInput = document.getElementById("share-url");
    if (shareUrlInput) {
        const url = new URL(window.location.href);
        url.searchParams.set("zip1", zip1);
        url.searchParams.set("zip2", zip2);
        shareUrlInput.value = url.toString();
    }
    
    // Display result card
    resultContainer.style.display = "block";
    resultContainer.classList.add("animate-fade-in");
    
    // Scroll results into view
    setTimeout(() => {
        resultContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, 100);
}

// Show Error Message helper
function showError(text) {
    const errorMsg = document.getElementById("error-message");
    const errorText = document.getElementById("error-text");
    if (!errorMsg || !errorText) return;
    
    errorText.textContent = text;
    errorMsg.style.display = "flex";
    errorMsg.classList.add("animate-fade-in");
}

// --- Random Address Generator Data & Logic ---

const COMMON_STREETS = [
    "Main", "Oak", "Pine", "Maple", "Cedar", "Elm", "View", "Washington", "Lake", "Hill",
    "Park", "Broadway", "Sunset", "Forest", "River", "Spring", "Cherry", "Dogwood", "Highland", "Ridge",
    "Meadow", "Jackson", "Lincoln", "Franklin", "Jefferson", "Adams", "Madison", "Monroe", "Wilson", "Taft",
    "Summit", "Valley", "Willow", "Birch", "Spruce", "Walnut", "Chestnut", "Hickory", "Laurel", "Magnolia",
    "Cypress", "Poplar", "Acorn", "Amber", "Autumn", "Beacon", "Bridle", "Brook", "Canyon", "Charter",
    "Cottage", "Crest", "Crown", "Diamond", "Eagle", "Falcon", "Garden", "Gateway", "Glen", "Grand",
    "Hampton", "Harvest", "Heritage", "Heather", "Ivy", "Jasmine", "Lakeside", "Lantern", "Legacy", "Liberty",
    "Linden", "Meadowbrook", "Mill", "North Star", "Orchard", "Overlook", "Pebble", "Pheasant", "Pleasant", "Promenade",
    "Quail", "Redwood", "Rose", "Serenade", "Shadow", "Sherwood", "Silver", "Skyline", "Stone", "Summer",
    "Timber", "Trillium", "Trinity", "Union", "Vanguard", "Victoria", "Windwood", "Woodland"
];

const STREET_SUFFIXES = ["St", "Ave", "Rd", "Ln", "Blvd", "Dr", "Ct", "Way", "Pl", "Ter"];

// Autocomplete specifically for the Random Address Generator input
function setupGenAutocomplete(inputId, suggestionsId) {
    const input = document.getElementById(inputId);
    const suggestionsBox = document.getElementById(suggestionsId);
    const clearBtn = document.getElementById("clear-gen");
    
    if (!input || !suggestionsBox) return;
    
    input.addEventListener("focus", loadSearchIndex);
    input.addEventListener("mouseenter", loadSearchIndex);
    
    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        
        if (query.length > 0) {
            if (clearBtn) clearBtn.style.display = "flex";
        } else {
            if (clearBtn) clearBtn.style.display = "none";
            suggestionsBox.style.display = "none";
            return;
        }
        
        if (!searchIndex) return;
        
        const matches = [];
        const maxSuggestions = 10;
        const isNumeric = /^\d+$/.test(query);
        
        // 1. Match States
        for (let s of searchIndex.states) {
            if (matches.length >= maxSuggestions) break;
            if (s.n.toLowerCase().includes(query) || s.a.toLowerCase() === query) {
                matches.push({
                    type: 'state',
                    title: s.n,
                    subtitle: `State (${s.a})`,
                    badge: 'State',
                    code: s.a,
                    name: s.n
                });
            }
        }
        
        // 2. Match Counties
        for (let c of searchIndex.counties) {
            if (matches.length >= maxSuggestions) break;
            if (c.n.toLowerCase().includes(query)) {
                matches.push({
                    type: 'county',
                    title: `${c.n} County, ${c.a}`,
                    subtitle: `County in ${c.st}`,
                    badge: 'County',
                    name: c.n,
                    state: c.a,
                    key: c.s
                });
            }
        }
        
        // 3. Match Cities and ZIPs
        const addedCities = new Set();
        let zipMatchCount = 0;
        
        for (let [zip, details] of Object.entries(searchIndex.zips)) {
            if (matches.length >= maxSuggestions) break;
            if (zipMatchCount >= 5) break;
            
            const [stateAbbr, county, city, lat, lon] = details;
            
            // Check ZIP match
            if (zip.startsWith(query)) {
                matches.push({
                    type: 'zip',
                    title: `${zip} - ${city}`,
                    subtitle: `${county} County, ${stateAbbr}`,
                    badge: 'ZIP Code',
                    code: zip,
                    city: city,
                    state: stateAbbr
                });
                zipMatchCount++;
                continue;
            }
            
            // Check City match (group unique city-state suggestions)
            if (!isNumeric && city.toLowerCase().includes(query)) {
                const cityKey = `${city.toLowerCase()}-${stateAbbr.toLowerCase()}`;
                if (!addedCities.has(cityKey)) {
                    addedCities.add(cityKey);
                    matches.push({
                        type: 'city',
                        title: `${city}, ${stateAbbr}`,
                        subtitle: `${county} County`,
                        badge: 'City',
                        name: city,
                        state: stateAbbr
                    });
                    zipMatchCount++;
                }
            }
        }
        
        // Render suggestions list
        if (matches.length === 0) {
            suggestionsBox.innerHTML = `
                <div style="padding: 12px 16px; font-size: 13px; color: var(--text-muted); text-align: center;">
                    No regions found for "<strong>${escapeHtml(query)}</strong>"
                </div>
            `;
        } else {
            let html = "";
            matches.slice(0, maxSuggestions).forEach((item, idx) => {
                let badgeClass = "suggestion-badge";
                let icon = "🗺️";
                if (item.type === 'county') {
                    icon = "📍";
                } else if (item.type === 'city') {
                    icon = "🏙️";
                } else if (item.type === 'zip') {
                    icon = "✉️";
                }
                
                html += `
                <div class="suggestion-item" style="padding: 10px 16px; cursor: pointer; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between;" data-idx="${idx}">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="suggestion-icon">${icon}</div>
                        <div>
                            <div style="font-weight: 600; color: var(--text-primary); font-size: 13px;">${item.title}</div>
                            <div style="font-size: 11px; color: var(--text-muted);">${item.subtitle}</div>
                        </div>
                    </div>
                    <span class="${badgeClass}">${item.badge}</span>
                </div>
                `;
            });
            suggestionsBox.innerHTML = html;
            
            // Add click events to suggestions
            const items = suggestionsBox.getElementsByClassName("suggestion-item");
            for (let item of items) {
                item.addEventListener("click", () => {
                    const idx = parseInt(item.getAttribute("data-idx"));
                    const selected = matches[idx];
                    
                    input.value = selected.title;
                    suggestionsBox.style.display = "none";
                    if (clearBtn) clearBtn.style.display = "flex";
                    
                    // Set active scope
                    window.generatorScope = selected;
                    
                    let scopeText = "United States (All)";
                    if (selected.type === 'state') {
                        scopeText = `State: ${selected.name}`;
                    } else if (selected.type === 'county') {
                        scopeText = `County: ${selected.name} (${selected.state})`;
                    } else if (selected.type === 'city') {
                        scopeText = `City: ${selected.name}, ${selected.state}`;
                    } else if (selected.type === 'zip') {
                        scopeText = `ZIP Code: ${selected.code} (${selected.city}, ${selected.state})`;
                    }
                    
                    document.getElementById("active-scope").querySelector("span strong").textContent = scopeText;
                    
                    // Generate new addresses instantly
                    triggerAddressGeneration();
                });
            }
        }
        suggestionsBox.style.display = "block";
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = "none";
        }
    });
}

// Generate 6 random addresses based on the current scope
async function triggerAddressGeneration() {
    const errorMsg = document.getElementById("gen-error-message");
    const container = document.getElementById("addresses-container");
    
    if (!container) return;
    if (errorMsg) errorMsg.style.display = "none";
    
    container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="animation: spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-opacity="0.25"></circle><path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <div style="margin-top: 10px; font-weight: 500;">Compiling Addresses...</div>
        </div>
    `;
    
    await loadSearchIndex();
    
    if (!searchIndex || !searchIndex.zips) {
        showGenError("Failed to load ZIP database.");
        return;
    }
    
    const scope = window.generatorScope || { type: 'all' };
    const filteredZips = [];
    
    // Filter matching ZIP codes
    for (let [zip, details] of Object.entries(searchIndex.zips)) {
        const [stateAbbr, county, city, lat, lon] = details;
        
        let match = false;
        if (scope.type === 'all') {
            // Filter out placeholders if they have no coordinates
            match = (lat !== null && lon !== null);
        } else if (scope.type === 'state') {
            match = (stateAbbr.toLowerCase() === scope.code.toLowerCase());
        } else if (scope.type === 'county') {
            match = (county.toLowerCase() === scope.name.toLowerCase() && stateAbbr.toLowerCase() === scope.state.toLowerCase());
        } else if (scope.type === 'city') {
            match = (city.toLowerCase() === scope.name.toLowerCase() && stateAbbr.toLowerCase() === scope.state.toLowerCase());
        } else if (scope.type === 'zip') {
            match = (zip === scope.code);
        }
        
        if (match) {
            filteredZips.push({
                zip: zip,
                city: city,
                county: county,
                state: stateAbbr,
                lat: lat,
                lon: lon
            });
        }
    }
    
    if (filteredZips.length === 0) {
        showGenError("No valid geographical ZIP codes found for the selected scope.");
        return;
    }
    
    // Choose 6 ZIPs randomly
    const chosen = [];
    for (let i = 0; i < 6; i++) {
        const randIdx = Math.floor(Math.random() * filteredZips.length);
        chosen.push(filteredZips[randIdx]);
    }
    
    // Compile and render addresses
    let html = "";
    chosen.forEach(item => {
        // Random street number: 10 - 9999
        const streetNum = Math.floor(Math.random() * 9980) + 10;
        
        // Random street name
        const streetName = COMMON_STREETS[Math.floor(Math.random() * COMMON_STREETS.length)];
        
        // Random suffix
        const suffix = STREET_SUFFIXES[Math.floor(Math.random() * STREET_SUFFIXES.length)];
        
        const streetAddress = `${streetNum} ${streetName} ${suffix}`;
        const cityStateZip = `${item.city}, ${item.state} ${item.zip}`;
        const fullFormattedAddress = `${streetAddress}\n${cityStateZip}`;
        const coordsText = (item.lat !== null && item.lon !== null) ? `${item.lat.toFixed(4)}, ${item.lon.toFixed(4)}` : "N/A";
        
        html += `
        <div class="state-card animate-fade-in" style="padding: 20px; border: 1px solid var(--border-color); background: var(--bg-secondary); box-shadow: var(--shadow-sm); display: flex; flex-direction: column; justify-content: space-between; border-radius: var(--card-radius); text-align: left;">
            <div>
                <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px; color: var(--primary-color);">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
                        <span style="font-weight: 700; font-size: 13px; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em;">Random Address</span>
                    </div>
                    <span class="state-abbr" style="background: var(--bg-tertiary); font-size: 11px; padding: 2px 6px;">${item.zip}</span>
                </div>
                
                <div style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; font-family: var(--font-heading);">${streetAddress}</div>
                <div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">${cityStateZip}</div>
                
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">County: <strong style="color: var(--text-secondary);">${item.county}</strong></div>
                <div style="font-size: 11px; color: var(--text-muted); font-family: monospace;">Centroid: ${coordsText}</div>
            </div>
            
            <button class="pill-btn active copy-address-btn" data-address="${escapeHtml(fullFormattedAddress)}" style="margin-top: 16px; width: 100%; font-size: 12px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                <span>Copy Address</span>
            </button>
        </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Bind copy clipboard event handlers to copy buttons
    const copyBtns = container.getElementsByClassName("copy-address-btn");
    for (let btn of copyBtns) {
        btn.addEventListener("click", () => {
            const text = btn.getAttribute("data-address");
            navigator.clipboard.writeText(text).then(() => {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = `
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="20 6 9 17 4 12"/></svg>
                    <span>Copied!</span>
                `;
                btn.style.backgroundColor = "#10b981"; // change to green
                btn.style.borderColor = "#10b981";
                
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                    btn.style.backgroundColor = ""; // reset
                    btn.style.borderColor = "";
                }, 2000);
            }).catch(err => {
                console.error("Failed to copy address: ", err);
            });
        });
    }
    
    // Update share url inputs
    const shareUrlInput = document.getElementById("gen-share-url");
    const shareContainer = document.getElementById("share-container");
    if (shareUrlInput && shareContainer) {
        const url = new URL(window.location.href);
        url.search = ""; // clear existing search query
        
        if (scope.type === 'zip') {
            url.searchParams.set("zip", scope.code);
        } else if (scope.type === 'state') {
            url.searchParams.set("state", scope.code);
        } else if (scope.type === 'county') {
            url.searchParams.set("county", scope.key);
        } else if (scope.type === 'city') {
            url.searchParams.set("city", scope.name);
        }
        
        if (scope.type !== 'all') {
            shareUrlInput.value = url.toString();
            shareContainer.style.display = "flex";
            shareContainer.classList.add("animate-fade-in");
        } else {
            shareContainer.style.display = "none";
        }
    }
}

// Show address generation error helper
function showGenError(text) {
    const errorMsg = document.getElementById("gen-error-message");
    const errorText = document.getElementById("gen-error-text");
    const container = document.getElementById("addresses-container");
    
    if (container) container.innerHTML = "";
    if (!errorMsg || !errorText) return;
    
    errorText.textContent = text;
    errorMsg.style.display = "flex";
    errorMsg.classList.add("animate-fade-in");
}

// --- ZIP Code Radius Finder & Geolocation Logic ---

// Setup Autocomplete for Radius Finder Input
function setupRadiusAutocomplete(inputId, suggestionsId) {
    const input = document.getElementById(inputId);
    const suggestionsBox = document.getElementById(suggestionsId);
    const clearBtn = document.getElementById("clear-radius");
    
    if (!input || !suggestionsBox) return;
    
    input.addEventListener("focus", loadSearchIndex);
    input.addEventListener("mouseenter", loadSearchIndex);
    
    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        
        if (query.length > 0) {
            if (clearBtn) clearBtn.style.display = "flex";
        } else {
            if (clearBtn) clearBtn.style.display = "none";
            suggestionsBox.style.display = "none";
            return;
        }
        
        if (!searchIndex) return;
        
        const matches = [];
        const maxSuggestions = 10;
        const isNumeric = /^\d+$/.test(query);
        
        // 1. Match Cities and ZIPs (exclude States and Counties for Radius)
        const addedCities = new Set();
        let zipMatchCount = 0;
        
        for (let [zip, details] of Object.entries(searchIndex.zips)) {
            if (matches.length >= maxSuggestions) break;
            if (zipMatchCount >= 8) break;
            
            const [stateAbbr, county, city, lat, lon] = details;
            
            // Check ZIP match
            if (zip.startsWith(query)) {
                matches.push({
                    type: 'zip',
                    title: `${zip} - ${city}`,
                    subtitle: `${county} County, ${stateAbbr}`,
                    badge: 'ZIP Code',
                    code: zip,
                    city: city,
                    state: stateAbbr,
                    lat: lat,
                    lon: lon
                });
                zipMatchCount++;
                continue;
            }
            
            // Check City match
            if (!isNumeric && city.toLowerCase().includes(query)) {
                const cityKey = `${city.toLowerCase()}-${stateAbbr.toLowerCase()}`;
                if (!addedCities.has(cityKey)) {
                    addedCities.add(cityKey);
                    matches.push({
                        type: 'city',
                        title: `${city}, ${stateAbbr}`,
                        subtitle: `${county} County`,
                        badge: 'City',
                        name: city,
                        state: stateAbbr,
                        lat: lat,
                        lon: lon
                    });
                    zipMatchCount++;
                }
            }
        }
        
        if (matches.length === 0) {
            suggestionsBox.innerHTML = `
                <div style="padding: 12px 16px; font-size: 13px; color: var(--text-muted); text-align: center;">
                    No matches found for "<strong>${escapeHtml(query)}</strong>"
                </div>
            `;
        } else {
            let html = "";
            matches.forEach((item, idx) => {
                const icon = item.type === 'zip' ? "✉️" : "🏙️";
                html += `
                <div class="suggestion-item" style="padding: 10px 16px; cursor: pointer; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between;" data-idx="${idx}">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div class="suggestion-icon">${icon}</div>
                        <div>
                            <div style="font-weight: 600; color: var(--text-primary); font-size: 13px;">${item.title}</div>
                            <div style="font-size: 11px; color: var(--text-muted);">${item.subtitle}</div>
                        </div>
                    </div>
                    <span class="suggestion-badge">${item.badge}</span>
                </div>
                `;
            });
            suggestionsBox.innerHTML = html;
            
            const items = suggestionsBox.getElementsByClassName("suggestion-item");
            for (let item of items) {
                item.addEventListener("click", () => {
                    const idx = parseInt(item.getAttribute("data-idx"));
                    const selected = matches[idx];
                    
                    input.value = selected.title;
                    suggestionsBox.style.display = "none";
                    if (clearBtn) clearBtn.style.display = "flex";
                    
                    window.radiusOriginScope = selected;
                    triggerRadiusSearch();
                });
            }
        }
        suggestionsBox.style.display = "block";
    });
    
    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = "none";
        }
    });
}

// Calculate and render all U.S. ZIP codes within the target radius
async function triggerRadiusSearch() {
    const originInput = document.getElementById("radius-origin");
    const radiusRange = document.getElementById("radius-range");
    const errorMsg = document.getElementById("radius-error-message");
    const resultsWrapper = document.getElementById("radius-results-wrapper");
    const tableBody = document.getElementById("radius-table-body");
    
    if (!originInput || !radiusRange || !tableBody) return;
    
    if (errorMsg) errorMsg.style.display = "none";
    resultsWrapper.style.display = "none";
    
    const query = originInput.value.trim();
    if (!query) {
        showRadiusError("Please enter a starting ZIP code or City.");
        return;
    }
    
    await loadSearchIndex();
    
    let originLat = null;
    let originLon = null;
    let originLabel = "";
    
    // Resolve starting coordinate
    if (window.radiusOriginScope && window.radiusOriginScope.lat !== null) {
        originLat = window.radiusOriginScope.lat;
        originLon = window.radiusOriginScope.lon;
        originLabel = window.radiusOriginScope.title;
    } else {
        // Attempt fallback lookup
        const isNumeric = /^\d+$/.test(query);
        if (isNumeric && query.length === 5) {
            const details = searchIndex.zips[query];
            if (details && details[3] !== null) {
                originLat = details[3];
                originLon = details[4];
                originLabel = `${query} - ${details[2]}, ${details[0]}`;
                window.radiusOriginScope = { type: 'zip', code: query, lat: originLat, lon: originLon, title: originLabel };
            }
        } else {
            // Find first matching city, supporting comma-separated inputs like "Los Angeles, CA"
            let cleanCityQuery = query.toLowerCase();
            if (cleanCityQuery.includes(",")) {
                cleanCityQuery = cleanCityQuery.split(",")[0].trim();
            }
            
            for (let [zip, details] of Object.entries(searchIndex.zips)) {
                if (details[2].toLowerCase() === cleanCityQuery && details[3] !== null) {
                    originLat = details[3];
                    originLon = details[4];
                    originLabel = `${details[2]}, ${details[0]}`;
                    window.radiusOriginScope = { type: 'city', name: details[2], lat: originLat, lon: originLon, title: originLabel };
                    break;
                }
            }
        }
    }
    
    if (originLat === null || originLon === null) {
        showRadiusError(`Could not find coordinates for "${query}". Please select a location from the autocomplete list.`);
        return;
    }
    
    const radiusMiles = parseFloat(radiusRange.value);
    const results = [];
    
    // Scan all U.S. ZIP codes
    for (let [zip, details] of Object.entries(searchIndex.zips)) {
        const [stateAbbr, county, city, lat, lon] = details;
        if (lat === null || lon === null) continue;
        
        const distObj = calculateHaversineDistance(originLat, originLon, lat, lon);
        const distance = distObj.miles;
        if (distance <= radiusMiles) {
            results.push({
                zip: zip,
                city: city,
                state: stateAbbr,
                county: county,
                distance: distance,
                lat: lat,
                lon: lon
            });
        }
    }
    
    if (results.length === 0) {
        showRadiusError("No ZIP codes found within the selected radius.");
        return;
    }
    
    // Sort closest first
    results.sort((a, b) => a.distance - b.distance);
    window.lastRadiusResults = results;
    
    // Render results
    let html = "";
    results.forEach(item => {
        html += `
        <tr style="border-bottom: 1px solid var(--border-color);">
            <td style="padding: 12px 16px; font-weight: 700; color: var(--primary-color);">${item.distance.toFixed(2)} mi</td>
            <td style="padding: 12px 16px;"><a href="county/${item.state.toLowerCase()}-${makeSlug(item.county)}.html#${item.zip}" style="font-weight: 600; text-decoration: underline;">${item.zip}</a></td>
            <td style="padding: 12px 16px;">${item.city}</td>
            <td style="padding: 12px 16px; font-weight: 600; color: var(--text-secondary);">${item.state}</td>
            <td style="padding: 12px 16px; color: var(--text-muted);">${item.county} County</td>
            <td style="padding: 12px 16px; font-family: monospace; font-size: 12px; color: var(--text-muted);">${item.lat.toFixed(4)}, ${item.lon.toFixed(4)}</td>
        </tr>
        `;
    });
    tableBody.innerHTML = html;
    
    document.getElementById("radius-results-title").innerHTML = `Found <strong>${results.length}</strong> ZIP codes within <strong>${radiusMiles} miles</strong> of <em>${originLabel}</em>`;
    resultsWrapper.style.display = "block";
    resultsWrapper.classList.add("animate-fade-in");
}

// Show radius error helper
function showRadiusError(text) {
    const errorMsg = document.getElementById("radius-error-message");
    const errorText = document.getElementById("radius-error-text");
    if (!errorMsg || !errorText) return;
    
    errorText.textContent = text;
    errorMsg.style.display = "flex";
    errorMsg.classList.add("animate-fade-in");
}

// Perform client-side browser GPS geolocation to match the nearest U.S. ZIP
async function findNearMe() {
    if (!navigator.geolocation) {
        showToast("Error: Geolocation is not supported by your browser.");
        return;
    }
    
    showToast("Requesting GPS coordinates...");
    
    navigator.geolocation.getCurrentPosition(async (position) => {
        const userLat = position.coords.latitude;
        const userLon = position.coords.longitude;
        
        showToast("Matching coordinates to database...");
        await loadSearchIndex();
        
        if (!searchIndex || !searchIndex.zips) {
            showToast("Failed to load geographic database.");
            return;
        }
        
        let closestZip = null;
        let minDistance = Infinity;
        let closestDetails = null;
        
        for (let [zip, details] of Object.entries(searchIndex.zips)) {
            const [stateAbbr, county, city, lat, lon] = details;
            if (lat === null || lon === null) continue;
            
            const distObj = calculateHaversineDistance(userLat, userLon, lat, lon);
            const dist = distObj.miles;
            if (dist < minDistance) {
                minDistance = dist;
                closestZip = zip;
                closestDetails = details;
            }
        }
        
        if (closestZip) {
            const [stateAbbr, county, city] = closestDetails;
            showToast(`Found nearest ZIP: ${closestZip} (${city}, ${stateAbbr}). Redirecting...`);
            
            // Generate path prefix based on directory context
            const pathPrefix = (window.location.pathname.includes('/state/') || window.location.pathname.includes('/county/')) ? '../county/' : 'county/';
            const countySlug = `${stateAbbr.toLowerCase()}-${makeSlug(county)}`;
            
            setTimeout(() => {
                window.location.href = `${pathPrefix}${countySlug}.html#${closestZip}`;
            }, 1200);
        } else {
            showToast("Could not find any nearby ZIP codes.");
        }
    }, (error) => {
        console.error(error);
        switch (error.code) {
            case error.PERMISSION_DENIED:
                showToast("GPS Permission Denied. Please enable location services.");
                break;
            case error.POSITION_UNAVAILABLE:
                showToast("Location details unavailable.");
                break;
            case error.TIMEOUT:
                showToast("GPS request timed out.");
                break;
            default:
                showToast("An unknown error occurred locating coordinates.");
        }
    });
}

// Client-Side CSV Generator and Downloader
function downloadListAsCSV(filename, headers, rows) {
    // Escape and wrap fields in quotes
    const escapeCsvField = (field) => {
        const text = String(field);
        if (text.includes('"') || text.includes(',') || text.includes('\n')) {
            return `"${text.replace(/"/g, '""')}"`;
        }
        return text;
    };
    
    let csvContent = headers.map(escapeCsvField).join(",") + "\n";
    rows.forEach(row => {
        csvContent += row.map(escapeCsvField).join(",") + "\n";
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// ----------------------------------------------------
// FEATURE 1: Interactive US State Explorer Map Widget
// ----------------------------------------------------
function initUSStateMap() {
    const tiles = document.querySelectorAll(".map-tile-btn");
    const badge = document.getElementById("map-state-badge");
    if (!tiles.length || !badge) return;
    
    tiles.forEach(tile => {
        tile.addEventListener("mouseenter", () => {
            const name = tile.getAttribute("data-name");
            const abbr = tile.getAttribute("data-abbr");
            const counties = tile.getAttribute("data-counties");
            const zips = tile.getAttribute("data-zips");
            badge.innerHTML = `<span>${name} (${abbr}) &bull; ${counties} Counties &bull; ${zips} ZIPs</span>`;
        });
        tile.addEventListener("mouseleave", () => {
            badge.innerHTML = `<span>Hover a State</span>`;
        });
    });
}

// ----------------------------------------------------
// FEATURE 2: USPS Address Standardizer & Formatter
// ----------------------------------------------------
function initAddressStandardizer() {
    const stdBtn = document.getElementById("standardize-btn");
    const sampleBtn = document.getElementById("sample-address-btn");
    const copyBtn = document.getElementById("copy-standardized-btn");
    const rawInput = document.getElementById("raw-address-input");
    const wrapper = document.getElementById("standardizer-result-wrapper");
    const output = document.getElementById("standardized-address-output");
    const rulesList = document.getElementById("applied-rules-list");
    
    if (!stdBtn || !rawInput) return;
    
    if (sampleBtn) {
        sampleBtn.addEventListener("click", () => {
            rawInput.value = "123 west main street apartment 4b, beverly hills, california 90210";
            triggerStandardization();
        });
    }
    
    stdBtn.addEventListener("click", triggerStandardization);
    
    if (copyBtn) {
        copyBtn.addEventListener("click", () => {
            if (output && output.textContent) {
                navigator.clipboard.writeText(output.textContent).then(() => {
                    showToast("Standardized address copied to clipboard!");
                });
            }
        });
    }
    
    function triggerStandardization() {
        const text = rawInput.value.trim();
        if (!text) return;
        
        let formatted = text.toUpperCase();
        const appliedRules = [];
        
        // 1. Convert State Full Names to Abbr
        const stateReplacements = {
            "CALIFORNIA": "CA", "NEW YORK": "NY", "TEXAS": "TX", "FLORIDA": "FL", "ILLINOIS": "IL",
            "PENNSYLVANIA": "PA", "OHIO": "OH", "GEORGIA": "GA", "NORTH CAROLINA": "NC", "MICHIGAN": "MI",
            "NEW JERSEY": "NJ", "VIRGINIA": "VA", "WASHINGTON": "WA", "MASSACHUSETTS": "MA", "ARIZONA": "AZ",
            "INDIANA": "IN", "TENNESSEE": "TN", "MISSOURI": "MO", "MARYLAND": "MD", "WISCONSIN": "WI",
            "COLORADO": "CO", "MINNESOTA": "MN", "SOUTH CAROLINA": "SC", "ALABAMA": "AL", "LOUISIANA": "LA",
            "KENTUCKY": "KY", "OREGON": "OR", "OKLAHOMA": "OK", "CONNECTICUT": "CT", "UTAH": "UT"
        };
        
        for (let [fullName, abbr] of Object.entries(stateReplacements)) {
            const reg = new RegExp(`\\b${fullName}\\b`, "g");
            if (reg.test(formatted)) {
                formatted = formatted.replace(reg, abbr);
                appliedRules.push(`State Name $\\rightarrow$ ${abbr}`);
            }
        }
        
        // 2. Street Suffixes
        const suffixRules = [
            [/\bSTREET\b/g, "ST", "STREET $\\rightarrow$ ST"],
            [/\bAVENUE\b/g, "AVE", "AVENUE $\\rightarrow$ AVE"],
            [/\bBOULEVARD\b/g, "BLVD", "BOULEVARD $\\rightarrow$ BLVD"],
            [/\bDRIVE\b/g, "DR", "DRIVE $\\rightarrow$ DR"],
            [/\bROAD\b/g, "RD", "ROAD $\\rightarrow$ RD"],
            [/\bLANE\b/g, "LN", "LANE $\\rightarrow$ LN"],
            [/\bCOURT\b/g, "CT", "COURT $\\rightarrow$ CT"],
            [/\bPLACE\b/g, "PL", "PLACE $\\rightarrow$ PL"],
            [/\bCIRCLE\b/g, "CIR", "CIRCLE $\\rightarrow$ CIR"],
            [/\bHIGHWAY\b/g, "HWY", "HIGHWAY $\\rightarrow$ HWY"],
            [/\bPARKWAY\b/g, "PKWY", "PARKWAY $\\rightarrow$ PKWY"]
        ];
        
        suffixRules.forEach(([reg, rep, desc]) => {
            if (reg.test(formatted)) {
                formatted = formatted.replace(reg, rep);
                appliedRules.push(desc);
            }
        });
        
        // 3. Directionals
        const dirRules = [
            [/\bNORTHWEST\b/g, "NW", "NORTHWEST $\\rightarrow$ NW"],
            [/\bNORTHEAST\b/g, "NE", "NORTHEAST $\\rightarrow$ NE"],
            [/\bSOUTHWEST\b/g, "SW", "SOUTHWEST $\\rightarrow$ SW"],
            [/\bSOUTHEAST\b/g, "SE", "SOUTHEAST $\\rightarrow$ SE"],
            [/\bNORTH\b/g, "N", "NORTH $\\rightarrow$ N"],
            [/\bSOUTH\b/g, "S", "SOUTH $\\rightarrow$ S"],
            [/\bEAST\b/g, "E", "EAST $\\rightarrow$ E"],
            [/\bWEST\b/g, "W", "WEST $\\rightarrow$ W"]
        ];
        
        dirRules.forEach(([reg, rep, desc]) => {
            if (reg.test(formatted)) {
                formatted = formatted.replace(reg, rep);
                appliedRules.push(desc);
            }
        });
        
        // 4. Secondary Unit Designators
        const unitRules = [
            [/\bAPARTMENT\b/g, "APT", "APARTMENT $\\rightarrow$ APT"],
            [/\bSUITE\b/g, "STE", "SUITE $\\rightarrow$ STE"],
            [/\bBUILDING\b/g, "BLDG", "BUILDING $\\rightarrow$ BLDG"],
            [/\bROOM\b/g, "RM", "ROOM $\\rightarrow$ RM"],
            [/\bFLOOR\b/g, "FL", "FLOOR $\\rightarrow$ FL"]
        ];
        
        unitRules.forEach(([reg, rep, desc]) => {
            if (reg.test(formatted)) {
                formatted = formatted.replace(reg, rep);
                appliedRules.push(desc);
            }
        });
        
        // Always upper case rule
        appliedRules.unshift("Converted to Uppercase");
        
        // Clean punctuation & line breaks
        let cleanLines = formatted.split(",").map(s => s.trim()).filter(Boolean);
        let finalOutput = cleanLines.join("\n");
        
        output.textContent = finalOutput;
        
        let badgesHtml = "";
        appliedRules.forEach(r => {
            badgesHtml += `<span style="background: var(--bg-tertiary); border: 1px solid var(--border-color); color: var(--text-primary); padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 500;">✓ ${r}</span>`;
        });
        rulesList.innerHTML = badgesHtml;
        
        wrapper.style.display = "block";
        wrapper.classList.add("animate-fade-in");
    }
}

// ----------------------------------------------------
// FEATURE 3: ZIP Code Side-by-Side Comparison Tool
// ----------------------------------------------------
function initZipCompare() {
    const cmpBtn = document.getElementById("compare-btn");
    const input1 = document.getElementById("cmp-zip1");
    const input2 = document.getElementById("cmp-zip2");
    const input3 = document.getElementById("cmp-zip3");
    const wrapper = document.getElementById("cmp-results-wrapper");
    const thead = document.getElementById("cmp-table-head");
    const tbody = document.getElementById("cmp-table-body");
    
    if (!cmpBtn || !input1) return;
    
    setupRadiusAutocomplete("cmp-zip1", "suggestions-cmp1");
    setupRadiusAutocomplete("cmp-zip2", "suggestions-cmp2");
    setupRadiusAutocomplete("cmp-zip3", "suggestions-cmp3");
    
    cmpBtn.addEventListener("click", async () => {
        await loadSearchIndex();
        
        const zip1 = input1.value.trim().substring(0, 5);
        const zip2 = input2.value.trim().substring(0, 5);
        const zip3 = input3.value.trim().substring(0, 5);
        
        const selectedZips = [zip1, zip2, zip3].filter(z => z && searchIndex.zips[z]);
        
        if (selectedZips.length < 2) {
            showToast("Please enter at least 2 valid 5-digit ZIP codes to compare.");
            return;
        }
        
        let headHtml = `<tr style="background: var(--bg-tertiary); border-bottom: 2px solid var(--border-color);">
            <th style="padding: 14px 18px; color: var(--text-primary); font-size: 14px;">Feature / Attribute</th>`;
        
        selectedZips.forEach(z => {
            headHtml += `<th style="padding: 14px 18px; color: var(--primary-color); font-size: 16px; font-weight: 700;">ZIP Code ${z}</th>`;
        });
        headHtml += `</tr>`;
        thead.innerHTML = headHtml;
        
        const zipDetails = selectedZips.map(z => {
            const [abbr, county, city, lat, lon] = searchIndex.zips[z];
            const tz = estimateTimeZone(lon, abbr);
            return { zip: z, abbr, county, city, lat, lon, tz };
        });
        
        const rows = [
            ["City / Town", zipDetails.map(d => d.city)],
            ["State", zipDetails.map(d => `${d.abbr}`)],
            ["County", zipDetails.map(d => `${d.county} County`)],
            ["Centroid Coordinates", zipDetails.map(d => `${d.lat.toFixed(4)}°, ${d.lon.toFixed(4)}°`)],
            ["Time Zone", zipDetails.map(d => d.tz.name)],
            ["UTC Offset", zipDetails.map(d => d.tz.offset)]
        ];
        
        let bodyHtml = "";
        rows.forEach(([label, vals]) => {
            bodyHtml += `<tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 12px 18px; font-weight: 600; color: var(--text-secondary); width: 220px;">${label}</td>`;
            vals.forEach(v => {
                bodyHtml += `<td style="padding: 12px 18px; color: var(--text-primary); font-weight: 500;">${v}</td>`;
            });
            bodyHtml += `</tr>`;
        });
        
        // Add distance calculation row
        if (zipDetails.length >= 2) {
            const dObj = calculateHaversineDistance(zipDetails[0].lat, zipDetails[0].lon, zipDetails[1].lat, zipDetails[1].lon);
            bodyHtml += `<tr style="background: var(--bg-tertiary); font-weight: 700;">
                <td style="padding: 12px 18px; color: var(--primary-color);">Distance to ZIP #1</td>
                <td style="padding: 12px 18px; color: var(--primary-color);">0.00 mi</td>
                <td style="padding: 12px 18px; color: var(--primary-color);">${dObj.miles.toFixed(2)} mi (${dObj.km.toFixed(2)} km)</td>`;
            if (zipDetails.length === 3) {
                const dObj3 = calculateHaversineDistance(zipDetails[0].lat, zipDetails[0].lon, zipDetails[2].lat, zipDetails[2].lon);
                bodyHtml += `<td style="padding: 12px 18px; color: var(--primary-color);">${dObj3.miles.toFixed(2)} mi (${dObj3.km.toFixed(2)} km)</td>`;
            }
            bodyHtml += `</tr>`;
        }
        
        tbody.innerHTML = bodyHtml;
        wrapper.style.display = "block";
        wrapper.classList.add("animate-fade-in");
    });
}

// Helper to estimate Time Zone by Longitude & State
function estimateTimeZone(lon, state) {
    if (state === 'AK') return { name: 'Alaska Time (AKST/AKDT)', offset: 'UTC-9', zone: 'America/Anchorage' };
    if (state === 'HI') return { name: 'Hawaii Standard Time (HST)', offset: 'UTC-10', zone: 'Pacific/Honolulu' };
    if (state === 'PR' || state === 'VI') return { name: 'Atlantic Standard Time (AST)', offset: 'UTC-4', zone: 'America/Puerto_Rico' };
    
    if (lon > -82.5) return { name: 'Eastern Time (EST/EDT)', offset: 'UTC-5', zone: 'America/New_York' };
    if (lon > -103.0) return { name: 'Central Time (CST/CDT)', offset: 'UTC-6', zone: 'America/Chicago' };
    if (lon > -115.0) return { name: 'Mountain Time (MST/MDT)', offset: 'UTC-7', zone: 'America/Denver' };
    return { name: 'Pacific Time (PST/PDT)', offset: 'UTC-8', zone: 'America/Los_Angeles' };
}

// ----------------------------------------------------
// FEATURE 4: Time Zone & Live Local Clock Finder
// ----------------------------------------------------
let clockInterval = null;

function initTimeZoneFinder() {
    const tzInput = document.getElementById("tz-origin");
    const tzBtn = document.getElementById("tz-search-btn");
    const wrapper = document.getElementById("tz-result-wrapper");
    const badge = document.getElementById("tz-zone-badge");
    const clock = document.getElementById("tz-clock-display");
    const sub = document.getElementById("tz-details-sub");
    
    if (!tzBtn || !tzInput) return;
    
    setupRadiusAutocomplete("tz-origin", "suggestions-tz");
    
    tzBtn.addEventListener("click", triggerTzLookup);
    tzInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") triggerTzLookup();
    });
    
    async function triggerTzLookup() {
        const query = tzInput.value.trim();
        if (!query) return;
        
        await loadSearchIndex();
        
        let zipMatch = query.substring(0, 5);
        let details = searchIndex.zips[zipMatch];
        
        if (!details) {
            // Find first matching city
            for (let [z, d] of Object.entries(searchIndex.zips)) {
                if (d[2].toLowerCase().includes(query.toLowerCase())) {
                    zipMatch = z;
                    details = d;
                    break;
                }
            }
        }
        
        if (!details || details[3] === null) {
            showToast("Could not find time zone for the entered location.");
            return;
        }
        
        const [state, county, city, lat, lon] = details;
        const tzInfo = estimateTimeZone(lon, state);
        
        if (clockInterval) clearInterval(clockInterval);
        
        badge.textContent = `${tzInfo.name} (${tzInfo.offset})`;
        sub.innerHTML = `Location: <strong>${city}, ${state}</strong> (${zipMatch}) &bull; ${county} County`;
        
        function updateClock() {
            try {
                const now = new Date();
                const timeStr = now.toLocaleTimeString("en-US", { timeZone: tzInfo.zone, hour12: true, hour: "2-digit", minute: "2-digit", second: "2-digit" });
                clock.textContent = timeStr;
            } catch (e) {
                clock.textContent = new Date().toLocaleTimeString();
            }
        }
        
        updateClock();
        clockInterval = setInterval(updateClock, 1000);
        
        wrapper.style.display = "block";
        wrapper.classList.add("animate-fade-in");
    }
}

// ----------------------------------------------------
// FEATURE 5: Phone Area Code Directory & ZIP Lookup
// ----------------------------------------------------
function initAreaCodeLookup() {
    const acInput = document.getElementById("ac-input");
    const acBtn = document.getElementById("ac-search-btn");
    const wrapper = document.getElementById("ac-result-wrapper");
    const title = document.getElementById("ac-header-title");
    const body = document.getElementById("ac-details-body");
    
    if (!acBtn || !acInput) return;
    
    const areaCodeDb = {
        "212": { state: "NY", region: "New York City (Manhattan)", cities: "New York", zips: "10001, 10002, 10003, 10010, 10019" },
        "310": { state: "CA", region: "West Los Angeles & South Bay", cities: "Beverly Hills, Santa Monica, Torrance, Malibu", zips: "90210, 90401, 90501" },
        "415": { state: "CA", region: "San Francisco & Marin County", cities: "San Francisco, San Rafael", zips: "94102, 94103, 94901" },
        "312": { state: "IL", region: "Central Chicago", cities: "Chicago (Downtown)", zips: "60601, 60602, 60603" },
        "305": { state: "FL", region: "Miami & Florida Keys", cities: "Miami, Miami Beach, Key West", zips: "33101, 33139, 33040" },
        "214": { state: "TX", region: "Dallas Metropolitan Area", cities: "Dallas, Irving, Plano", zips: "75201, 75038, 75023" },
        "206": { state: "WA", region: "Seattle & Mercer Island", cities: "Seattle, Bainbridge Island", zips: "98101, 98104, 98115" },
        "404": { state: "GA", region: "Atlanta Metropolitan Area", cities: "Atlanta, Sandy Springs", zips: "30301, 30303, 30328" },
        "617": { state: "MA", region: "Boston & Eastern Massachusetts", cities: "Boston, Cambridge, Quincy", zips: "02108, 02138, 02169" },
        "702": { state: "NV", region: "Las Vegas Valley", cities: "Las Vegas, Henderson, Paradise", zips: "89101, 89014, 89109" },
        "602": { state: "AZ", region: "Phoenix Central Area", cities: "Phoenix", zips: "85001, 85004, 85016" },
        "713": { state: "TX", region: "Central Houston Area", cities: "Houston, Pasadena", zips: "77001, 77002, 77502" },
        "215": { state: "PA", region: "Philadelphia & Southeastern PA", cities: "Philadelphia, Levittown", zips: "19102, 19104, 19054" },
        "303": { state: "CO", region: "Denver Metro Area", cities: "Denver, Aurora, Lakewood", zips: "80201, 80012, 80226" },
        "512": { state: "TX", region: "Austin Capital Area", cities: "Austin, Round Rock, San Marcos", zips: "78701, 78664, 78666" },
        "615": { state: "TN", region: "Nashville & Central Tennessee", cities: "Nashville, Murfreesboro", zips: "37201, 37127" },
        "504": { state: "LA", region: "New Orleans Area", cities: "New Orleans, Metairie", zips: "70112, 70001" },
        "412": { state: "PA", region: "Pittsburgh & Allegheny County", cities: "Pittsburgh, Bethel Park", zips: "15201, 15102" },
        "313": { state: "MI", region: "Detroit & Wayne County", cities: "Detroit, Dearborn", zips: "48201, 48120" },
        "612": { state: "MN", region: "Minneapolis Area", cities: "Minneapolis, Richfield", zips: "55401, 55423" }
    };
    
    acBtn.addEventListener("click", triggerAcLookup);
    acInput.addEventListener("keyup", (e) => {
        if (acInput.value.length === 3 || e.key === "Enter") triggerAcLookup();
    });
    
    function triggerAcLookup() {
        const code = acInput.value.trim();
        if (!code || code.length !== 3) {
            showToast("Please enter a valid 3-digit area code.");
            return;
        }
        
        const data = areaCodeDb[code];
        if (data) {
            title.innerHTML = `Area Code (${code}) &bull; ${data.state} - ${data.region}`;
            body.innerHTML = `
                <div><strong>Primary State:</strong> ${data.state}</div>
                <div><strong>Major Cities Covered:</strong> ${data.cities}</div>
                <div><strong>Representative ZIP Codes:</strong> ${data.zips}</div>
                <div style="margin-top: 12px;"><a href="state/${data.state.toLowerCase()}.html" style="font-weight: 600; text-decoration: underline; color: var(--primary-color);">Browse All ${data.state} Counties & ZIP Codes &rarr;</a></div>
            `;
        } else {
            title.innerHTML = `Area Code (${code}) Information`;
            body.innerHTML = `<div>Area code <strong>${code}</strong> is assigned within North American Numbering Plan. Select a state directory to view specific regional postal mappings.</div>`;
        }
        
        wrapper.style.display = "block";
        wrapper.classList.add("animate-fade-in");
    }
}



