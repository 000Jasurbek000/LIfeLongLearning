// Mobile Menu Toggle
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navMenu = document.querySelector('.nav-menu');

if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        mobileMenuToggle.classList.toggle('active');
    });
}

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Header Scroll Effect - Dynamic color change
const header = document.querySelector('.header');
const headerSections = [...document.querySelectorAll('[data-header-style]')];

function updateHeaderColor() {
    if (!header || headerSections.length === 0) {
        return;
    }

    const headerHeight = header.offsetHeight;
    const triggerPoint = window.scrollY + headerHeight + 24;

    let activeSection = headerSections[0];

    headerSections.forEach((section) => {
        if (triggerPoint >= section.offsetTop) {
            activeSection = section;
        }
    });

    const headerStyle = activeSection.dataset.headerStyle;

    if (headerStyle === 'accent') {
        header.classList.add('scrolled-white');
    } else {
        header.classList.remove('scrolled-white');
    }
}

window.addEventListener('scroll', updateHeaderColor);
window.addEventListener('resize', updateHeaderColor);
window.addEventListener('load', updateHeaderColor);

// Animate on Scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all cards
document.querySelectorAll('.feature-card, .article-card').forEach(card => {
    observer.observe(card);
});

// Form Validation (for submit article page)
const validateForm = (formId) => {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const inputs = form.querySelectorAll('input[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('error');
            } else {
                input.classList.remove('error');
            }
        });
        
        if (isValid) {
            // Submit form
            console.log('Form submitted successfully');
            form.submit();
        } else {
            alert('Iltimos, barcha majburiy maydonlarni to\'ldiring');
        }
    });
};

// Counter Animation
const animateCounter = (element, target, duration = 2000) => {
    let start = 0;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target + '+';
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(start) + '+';
        }
    }, 16);
};

// Animate stats when visible
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = document.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const target = parseInt(stat.textContent);
                if (!isNaN(target)) {
                    animateCounter(stat, target);
                }
            });
            statsObserver.disconnect();
        }
    });
}, { threshold: 0.5 });

const statsSection = document.querySelector('.hero-stats');
if (statsSection) {
    statsObserver.observe(statsSection);
}

// Dropdown menu for mobile
document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024) {
            e.preventDefault();
            const dropdown = toggle.parentElement;
            dropdown.classList.toggle('active');
        }
    });
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.active').forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }
});

// Loading animation
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});

// ==========================================
// Advanced Search Functionality
// ==========================================
const searchToggle = document.querySelector('.search-toggle');
const searchPanel = document.querySelector('.search-panel');
const searchClose = document.querySelector('.search-close');
const searchOverlay = document.querySelector('.search-overlay');
const searchInput = document.querySelector('#searchInput');
const searchClear = document.querySelector('.search-clear');
const searchFilter = document.querySelector('#searchFilter');
const suggestionTags = document.querySelectorAll('.suggestion-tag');

// Open search panel
if (searchToggle) {
    searchToggle.addEventListener('click', () => {
        searchPanel.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            searchInput.focus();
        }, 300);
    });
}

// Close search panel
const closeSearchPanel = () => {
    searchPanel.classList.remove('active');
    document.body.style.overflow = '';
};

if (searchClose) {
    searchClose.addEventListener('click', closeSearchPanel);
}

if (searchOverlay) {
    searchOverlay.addEventListener('click', closeSearchPanel);
}

// Close with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && searchPanel.classList.contains('active')) {
        closeSearchPanel();
    }
});

// Search input clear button
if (searchInput && searchClear) {
    searchInput.addEventListener('input', () => {
        if (searchInput.value.length > 0) {
            searchClear.style.display = 'flex';
        } else {
            searchClear.style.display = 'none';
        }
    });
    
    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchClear.style.display = 'none';
        searchInput.focus();
    });
}

// Search filter update placeholder
if (searchFilter && searchInput) {
    const updatePlaceholder = () => {
        const selectedOption = searchFilter.options[searchFilter.selectedIndex];
        const placeholders = {
            'title': 'Maqola sarlavhasini kiriting...',
            'author': 'Muallif ismini kiriting...',
            'keywords': 'Kalit so\'zlarni kiriting...',
            'all': 'Qidiring...'
        };
        searchInput.placeholder = placeholders[searchFilter.value] || 'Qidiring...';
    };
    
    searchFilter.addEventListener('change', updatePlaceholder);
    updatePlaceholder();
}

// Suggestion tags
suggestionTags.forEach(tag => {
    tag.addEventListener('click', () => {
        searchInput.value = tag.textContent;
        searchInput.focus();
    });
});

// Search submit — redirect to backend qidiruv
const searchSubmitBtn = document.querySelector('.search-submit-btn');
if (searchSubmitBtn) {
    searchSubmitBtn.addEventListener('click', () => {
        const query = searchInput ? searchInput.value.trim() : '';
        const filter = searchFilter ? searchFilter.value : 'all';
        const baseUrl = searchSubmitBtn.dataset.searchUrl || '/qidiruv/';

        if (query) {
            const params = new URLSearchParams({ q: query, filter });
            window.location.href = `${baseUrl}?${params.toString()}`;
        } else if (searchInput) {
            searchInput.focus();
        }
    });
}

// Search on Enter key
if (searchInput) {
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchSubmitBtn.click();
        }
    });
}

// ==========================================
// Language Selector
// ==========================================
const languageSelector = document.querySelector('.language-selector');
const languageToggle = document.querySelector('.language-toggle');

if (languageSelector && languageToggle) {
    languageToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = languageSelector.classList.toggle('open');
        languageToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.language-selector')) {
            languageSelector.classList.remove('open');
            languageToggle.setAttribute('aria-expanded', 'false');
        }
    });
}

console.log('Ilmiy Jurnal - Website Loaded Successfully!');