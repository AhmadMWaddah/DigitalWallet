/**
 * --#-- Digital Wallet - Utility Functions
 *
 * Common JavaScript utilities for the Digital Wallet Dashboard.
 */

// --#-- DOM Ready Helper
function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

// --#-- Format Currency
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// --#-- Format Date
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

// --#-- Format Time
function formatTime(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// --#-- Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// --#-- Throttle Function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// --#-- Copy to Clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
}

// --#-- Show Toast Notification
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.position = 'fixed';
    toast.style.top = '80px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';

    toast.innerHTML = `
        <div class="alert-content">
            <span class="alert-message">${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// --#-- Confirm Dialog
function confirmAction(message = 'Are you sure?') {
    return window.confirm(message);
}

// --#-- Get Cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// --#-- Sidebar: Collapse (desktop) + Drawer (mobile), persisted
ready(() => {
    const app = document.getElementById('app');
    const sidebar = document.getElementById('sidebar');
    const collapseBtn = document.getElementById('sidebar-toggle');
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const backdrop = document.getElementById('sidebar-backdrop');

    if (collapseBtn && app) {
        collapseBtn.addEventListener('click', () => {
            app.classList.toggle('sidebar-collapsed');
            try {
                localStorage.setItem(
                    'sidebar-collapsed',
                    app.classList.contains('sidebar-collapsed') ? '1' : '0'
                );
            } catch (e) { /* private mode: no persistence */ }
        });
    }

    const closeDrawer = () => {
        if (sidebar) sidebar.classList.remove('active');
        if (backdrop) backdrop.classList.remove('visible');
    };

    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('active');
            if (backdrop) backdrop.classList.toggle('visible', sidebar.classList.contains('active'));
        });

        if (backdrop) backdrop.addEventListener('click', closeDrawer);

        // Close drawer when clicking outside
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('active')
                && !sidebar.contains(e.target)
                && !menuToggle.contains(e.target)) {
                closeDrawer();
            }
        });
    }
});

// --#-- Theme Toggle (light/dark, persists in localStorage; icon swap is pure CSS)
function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try {
        localStorage.setItem('theme', theme);
    } catch (e) { /* private mode: theme just won't persist */ }
}

ready(() => {
    const toggleBtn = document.querySelector('#theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.dataset.theme || 'light';
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }
});

// --#-- Chart.js Lazy Load (analytics canvases only)
ready(() => {
    const canvas = document.querySelector('canvas[data-chart]');
    if (!canvas || typeof loadChartJs !== 'function') return;
    if (!('IntersectionObserver' in window)) { loadChartJs(); return; }
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            loadChartJs();
            observer.disconnect();
        }
    });
    observer.observe(canvas);
});

// --#-- Modal: close on overlay click
ready(() => {
    document.addEventListener('click', (e) => {
        if (e.target.classList && e.target.classList.contains('modal-overlay')) {
            const container = document.getElementById('modal-container');
            if (container) container.innerHTML = '';
        }
    });
});
