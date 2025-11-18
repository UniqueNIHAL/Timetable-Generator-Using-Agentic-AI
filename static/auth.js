// Authentication Logic
let currentUser = null;
let userToken = null;
let firebaseReady = false;

// Check if Firebase is already ready (in case module loaded before this script)
function checkFirebaseReady() {
    if (window.firebaseReady && window.firebaseAuth && window.signInWithEmailAndPassword) {
        firebaseReady = true;
        console.log('Firebase already ready');
        initializeAuth();
        return true;
    }
    return false;
}

// Wait for Firebase to be ready
window.addEventListener('firebaseReady', () => {
    firebaseReady = true;
    console.log('Firebase ready event received in auth.js');
    initializeAuth();
});

// Try immediate check
if (!checkFirebaseReady()) {
    // If not ready yet, poll for a few seconds as fallback
    console.log('Firebase not ready yet, waiting...');
    let pollCount = 0;
    const pollInterval = setInterval(() => {
        pollCount++;
        if (checkFirebaseReady()) {
            clearInterval(pollInterval);
        } else if (pollCount > 50) { // 5 seconds max (50 * 100ms)
            clearInterval(pollInterval);
            console.error('Firebase failed to load after 5 seconds');
            showAuthError('Failed to load authentication. Please refresh the page.', 'login');
        }
    }, 100);
}

function initializeAuth() {
    // Set up auth state listener
    if (window.onAuthStateChanged && window.firebaseAuth) {
        window.onAuthStateChanged(async (user) => {
            if (user) {
                currentUser = user;
                userToken = await user.getIdToken();
                updateUserProfile(user);
                hideAuthModal();
                enableAuthenticatedFeatures();
                document.getElementById('main-app').style.display = 'block';
                console.log('User authenticated:', user.email);
            } else {
                currentUser = null;
                userToken = null;
                updateUserProfile(null);
                disableAuthenticatedFeatures();
                document.getElementById('main-app').style.display = 'none';
                showAuthModal();
                console.log('User signed out');
            }
        });
    }
}

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
    
    if (!window.firebaseReady || !window.signInWithEmailAndPassword) {
        showAuthError('Authentication system is still loading. Please wait a moment...', 'login');
        // Retry after 1 second
        setTimeout(() => {
            if (window.firebaseReady && window.signInWithEmailAndPassword) {
                loginWithEmail(event);
            }
        }, 1000);
        return;
    }
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const userCredential = await window.signInWithEmailAndPassword(email, password);
        await handleAuthSuccess(userCredential.user);
    } catch (error) {
        showAuthError(error.message, 'login');
    }
}

// Email/Password Signup
async function signupWithEmail(event) {
    event.preventDefault();
    
    if (!window.firebaseReady || !window.createUserWithEmailAndPassword) {
        showAuthError('Authentication system is still loading. Please wait a moment...', 'signup');
        return;
    }
    
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
        const userCredential = await window.createUserWithEmailAndPassword(email, password);
        await handleAuthSuccess(userCredential.user);
    } catch (error) {
        showAuthError(error.message, 'signup');
    }
}

// Google Sign-In
async function signInWithGoogle() {
    if (!window.firebaseReady || !window.signInWithPopup) {
        showAuthError('Authentication system is still loading. Please wait a moment...', 'login');
        return;
    }
    
    try {
        console.log('Attempting Google sign-in...', { 
            provider: window.googleProvider, 
            signInWithPopup: typeof window.signInWithPopup 
        });
        const result = await window.signInWithPopup(window.googleProvider);
        console.log('Google sign-in successful:', result.user.email);
        await handleAuthSuccess(result.user);
    } catch (error) {
        console.error('Google sign-in error:', error);
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
        await window.signOut();
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
