/**
 * Authentication functionality
 */

// Check authentication status on load
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.passwordSet && !data.authenticated) {
            // Show login form
            showLoginForm();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

function showLoginForm() {
    const loginHtml = `
        <div class="modal fade show" id="loginModal" tabindex="-1" style="display: block; background: rgba(0,0,0,0.8);">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content glass-card">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-shield-lock"></i> Authentication Required
                        </h5>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-control" id="authPassword" placeholder="Enter password">
                        </div>
                        <div id="authError" class="alert alert-danger" style="display: none;"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="doLogin()">
                            <i class="bi bi-unlock"></i> Login
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', loginHtml);
    
    // Focus password field
    document.getElementById('authPassword').focus();
    
    // Enter key to login
    document.getElementById('authPassword').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doLogin();
    });
}

async function doLogin() {
    const password = document.getElementById('authPassword').value;
    const errorDiv = document.getElementById('authError');
    
    if (!password) {
        errorDiv.textContent = 'Please enter a password';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({password})
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close modal and reload
            document.getElementById('loginModal').remove();
            
            if (data.envVar) {
                // First time setup
                alert(`Password set! Add this to your .env file:\n\n${data.envVar}`);
            } else {
                // Logged in successfully
                location.reload();
            }
        } else {
            errorDiv.textContent = data.error || 'Login failed';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = 'Login error: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// Add logout button if authenticated
function addLogoutButton() {
    const nav = document.querySelector('.navbar > div');
    if (nav && !document.getElementById('logoutBtn')) {
        const logoutBtn = document.createElement('button');
        logoutBtn.id = 'logoutBtn';
        logoutBtn.className = 'btn btn-outline-light btn-sm ms-2';
        logoutBtn.innerHTML = '<i class="bi bi-box-arrow-right"></i> Logout';
        logoutBtn.onclick = doLogout;
        nav.appendChild(logoutBtn);
    }
}

async function doLogout() {
    try {
        await fetch('/api/auth/logout', {method: 'POST'});
        location.reload();
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// Initialize authentication
if (typeof USE_AUTH !== 'undefined' && USE_AUTH) {
    document.addEventListener('DOMContentLoaded', () => {
        checkAuthStatus();
        addLogoutButton();
    });
}