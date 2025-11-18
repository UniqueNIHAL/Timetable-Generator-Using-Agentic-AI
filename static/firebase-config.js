// Firebase Configuration
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDicTdIoj8XZNNsK_39dz2IKjMiihw400E",
  authDomain: "bnb-blr-478413.firebaseapp.com",
  projectId: "bnb-blr-478413",
  storageBucket: "bnb-blr-478413.firebasestorage.app",
  messagingSenderId: "864636725010",
  appId: "1:864636725010:web:8fca3d126444b6f531f5cb"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Export for use in other files
window.firebaseAuth = auth;
window.googleProvider = googleProvider;
window.signInWithEmailAndPassword = signInWithEmailAndPassword;
window.createUserWithEmailAndPassword = createUserWithEmailAndPassword;
window.signInWithPopup = signInWithPopup;
window.signOut = signOut;
window.onAuthStateChanged = onAuthStateChanged;
