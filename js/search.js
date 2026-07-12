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


