// Firebase Configuration - Using CDN
// Import from the correct CDN URLs for Firebase v10.7.1
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { 
    getAuth, 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword, 
    signInWithPopup, 
    GoogleAuthProvider, 
    signOut, 
    onAuthStateChanged 
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDicTdIoj8XZNNsK_39dz2IKjMiihw400E",
  authDomain: "bnb-blr-478413.firebaseapp.com",
  projectId: "bnb-blr-478413",
  storageBucket: "bnb-blr-478413.firebasestorage.app",
  messagingSenderId: "864636725010",
  appId: "1:864636725010:web:8fca3d126444b6f531f5cb"
};

// Export immediately to window - BEFORE initialization
window.firebaseReady = false;
window.firebaseAuth = null;
window.googleProvider = null;

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Store the original Firebase functions
const _signInWithEmailAndPassword = signInWithEmailAndPassword;
const _createUserWithEmailAndPassword = createUserWithEmailAndPassword;
const _signInWithPopup = signInWithPopup;
const _signOut = signOut;
const _onAuthStateChanged = onAuthStateChanged;

// Create the auth wrapper functions using the stored originals
const authFunctions = {
    signInWithEmailAndPassword: (email, password) => _signInWithEmailAndPassword(auth, email, password),
    createUserWithEmailAndPassword: (email, password) => _createUserWithEmailAndPassword(auth, email, password),
    signInWithPopup: (provider) => _signInWithPopup(auth, provider),
    signOut: () => _signOut(auth),
    onAuthStateChanged: (callback) => _onAuthStateChanged(auth, callback)
};

// Now set them to window
window.firebaseAuth = auth;
window.googleProvider = googleProvider;
window.firebaseAuthFunctions = authFunctions;

// Export individual functions
window.signInWithEmailAndPassword = authFunctions.signInWithEmailAndPassword;
window.createUserWithEmailAndPassword = authFunctions.createUserWithEmailAndPassword;
window.signInWithPopup = authFunctions.signInWithPopup;
window.signOut = authFunctions.signOut;
window.onAuthStateChanged = authFunctions.onAuthStateChanged;

// Mark as ready
window.firebaseReady = true;

// Dispatch event to signal Firebase is ready
window.dispatchEvent(new Event('firebaseReady'));
console.log('Firebase initialized and ready', { 
    auth: !!window.firebaseAuth, 
    signIn: typeof window.signInWithEmailAndPassword,
    provider: !!window.googleProvider 
});
