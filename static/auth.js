// Authentication Logic
let currentUser = null;
let userToken = null;

// Show/Hide auth modal
function showAuthModal() {
    document.getElementById('auth-modal').classList.add('active');
}

function hideAuthModal() {
    // Only allow closing if user is logged in
    if (currentUser) {
        document.getElementById('auth-modal').classList.remove('active');
    }
}

// Switch between login and signup tabs
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    
    if (tab === 'login') {
        document.querySelector('[data-tab="login"]').classList.add('active');
        document.getElementById('login-form').classList.add('active');
    } else {
        document.querySelector('[data-tab="signup"]').classList.add('active');
        document.getElementById('signup-form').classList.add('active');
    }
}

// Show error message
function showAuthError(message, formId) {
    const errorDiv = document.getElementById(`${formId}-error`);
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
    setTimeout(() => errorDiv.classList.remove('show'), 5000);
}

// Email/Password Login
async function loginWithEmail(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const userCredential = await window.signInWithEmailAndPassword(window.firebaseAuth, email, password);
        await handleAuthSuccess(userCredential.user);
    } catch (error) {
        showAuthError(error.message, 'login');
    }
}

// Email/Password Signup
async function signupWithEmail(event) {
    event.preventDefault();
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    
    if (password !== confirmPassword) {
        showAuthError('Passwords do not match', 'signup');
        return;
    }
    
    if (password.length < 6) {
        showAuthError('Password must be at least 6 characters', 'signup');
        return;
    }
    
    try {
        const userCredential = await window.createUserWithEmailAndPassword(window.firebaseAuth, email, password);
        await handleAuthSuccess(userCredential.user);
    } catch (error) {
        showAuthError(error.message, 'signup');
    }
}

// Google Sign-In
async function signInWithGoogle() {
    try {
        const result = await window.signInWithPopup(window.firebaseAuth, window.googleProvider);
        await handleAuthSuccess(result.user);
    } catch (error) {
        showAuthError(error.message, 'login');
    }
}

// Handle successful authentication
async function handleAuthSuccess(user) {
    currentUser = user;
    userToken = await user.getIdToken();
    
    // Update UI
    hideAuthModal();
    updateUserProfile(user);
    
    // Show main app
    document.getElementById('main-app').style.display = 'block';
    
    // Show success message
    showFloatingNotification(`✅ Welcome, ${user.email}!`);
    
    // Enable features
    enableAuthenticatedFeatures();
}

// Update user profile display
function updateUserProfile(user) {
    const profileDiv = document.getElementById('user-profile');
    const loginButton = document.getElementById('login-button');
    
    if (user) {
        profileDiv.classList.add('active');
        loginButton.style.display = 'none';
        
        // Set user info
        document.getElementById('user-name').textContent = user.displayName || user.email.split('@')[0];
        document.getElementById('user-email').textContent = user.email;
        
        // Set avatar (first letter of email)
        document.getElementById('user-avatar').textContent = user.email.charAt(0).toUpperCase();
    } else {
        profileDiv.classList.remove('active');
        loginButton.style.display = 'block';
    }
}

// Logout
async function logout() {
    try {
        await window.signOut(window.firebaseAuth);
        currentUser = null;
        userToken = null;
        updateUserProfile(null);
        disableAuthenticatedFeatures();
        showFloatingNotification('👋 Logged out successfully');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Enable features for authenticated users
function enableAuthenticatedFeatures() {
    // Enable all functionality
    document.querySelectorAll('.auth-required').forEach(el => {
        el.style.pointerEvents = 'auto';
        el.style.opacity = '1';
    });
}

// Disable features (show login prompt)
function disableAuthenticatedFeatures() {
    document.querySelectorAll('.auth-required').forEach(el => {
        el.style.pointerEvents = 'none';
        el.style.opacity = '0.5';
    });
}

// Check if user is required to be authenticated for this action
function requireAuth(callback) {
    return function(...args) {
        if (!currentUser) {
            showFloatingNotification('⚠️ Please login to use this feature');
            showAuthModal();
            return;
        }
        return callback.apply(this, args);
    };
}

// Get auth token for API calls
function getAuthToken() {
    return userToken;
}

// Expose to window for use in other scripts
window.getAuthToken = getAuthToken;

// Listen for auth state changes
window.onAuthStateChanged(window.firebaseAuth, async (user) => {
    if (user) {
        currentUser = user;
        userToken = await user.getIdToken();
        updateUserProfile(user);
        enableAuthenticatedFeatures();
        hideAuthModal();
        // Show main content
        document.getElementById('main-app').style.display = 'block';
    } else {
        currentUser = null;
        userToken = null;
        updateUserProfile(null);
        disableAuthenticatedFeatures();
        // Hide main content and force login
        document.getElementById('main-app').style.display = 'none';
        showAuthModal();
    }
});

// Initialize auth on page load
document.addEventListener('DOMContentLoaded', () => {
    // Hide main content initially until auth check completes
    document.getElementById('main-app').style.display = 'none';
    
    // Close modal when clicking outside (only if logged in)
    document.getElementById('auth-modal').addEventListener('click', (e) => {
        if (e.target.id === 'auth-modal' && currentUser) {
            hideAuthModal();
        }
    });
});
