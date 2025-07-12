/**
 * Security utilities for the application
 */

// Store original fetch globally before any overrides
window.originalFetch = window.originalFetch || window.fetch;

// HTML escape function to prevent XSS
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Get CSRF token from meta tag or cookie
function getCSRFToken() {
    // First try meta tag
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) return token.content;
    
    // Then try cookie
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

// Fetch with CSRF token
async function secureFetch(url, options = {}) {
    const csrfToken = getCSRFToken();
    
    // Add CSRF token to headers
    if (!options.headers) {
        options.headers = {};
    }
    options.headers['X-CSRFToken'] = csrfToken;
    
    // Add JSON content type if sending JSON
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    
    // Use the original fetch to avoid recursion
    return window.originalFetch ? window.originalFetch(url, options) : fetch(url, options);
}

// Initialize CSRF token on page load
async function initializeCSRF() {
    try {
        const response = await fetch('/api/csrf-token');
        const data = await response.json();
        
        // Store in meta tag
        let meta = document.querySelector('meta[name="csrf-token"]');
        if (!meta) {
            meta = document.createElement('meta');
            meta.name = 'csrf-token';
            document.head.appendChild(meta);
        }
        meta.content = data.csrf_token;
    } catch (error) {
        console.error('Failed to get CSRF token:', error);
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCSRF);
} else {
    initializeCSRF();
}