# Firebase Authentication Setup

## Overview
The Agentic Timetable Planner now has Firebase Authentication integrated, requiring users to sign in before using key features.

## Features Implemented

### Frontend (Client-Side)
1. **Authentication Modal** (`static/index.html`)
   - Login/Signup forms with email/password
   - Google Sign-In integration
   - User profile display in header
   - Login/Logout buttons

2. **Firebase Configuration** (`static/firebase-config.js`)
   - Initialized Firebase SDK v10.7.1
   - Connected to project: `bnb-blr-478413`
   - Exports auth methods globally

3. **Auth Logic** (`static/auth.js`)
   - `loginWithEmail()` - Email/password login
   - `signupWithEmail()` - Create new accounts
   - `signInWithGoogle()` - Google OAuth flow
   - `logout()` - Sign out current user
   - `getAuthToken()` - Get ID token for API calls
   - `requireAuth()` - Protect features for logged-in users
   - Auto-displays login modal when not authenticated

4. **API Integration** (`static/app.js`)
   - All API requests include `Authorization: Bearer <token>` header
   - Protected endpoints: chat, generate, upload (all types)
   - Automatic token retrieval before API calls

### Backend (Server-Side)
1. **Firebase Auth Service** (`services/firebase_auth.py`)
   - `initialize_firebase()` - Load service account credentials
   - `verify_firebase_token()` - Validate ID tokens from clients
   - `get_current_user()` - Extract user from request headers
   - `@auth_required` - Decorator to protect endpoints
   - `@optional_auth` - Decorator for optional authentication

2. **Protected Endpoints** (`main.py`)
   - ✅ `/api/chat` - Chat with AI assistant
   - ✅ `/api/generate-timetable` - Generate timetables
   - ✅ `/api/upload/faculty` - Upload faculty data
   - ✅ `/api/upload/subjects` - Upload subjects data
   - ✅ `/api/upload/classrooms` - Upload classrooms data
   - ✅ `/api/upload/sections` - Upload sections data

3. **User Tracking**
   - Rate limiting per user UID (20 req/min)
   - User info available in `request.state.user`
   - Contains: `uid`, `email`, `name`, `email_verified`

## Configuration

### Environment Variables
```bash
# Set path to service account JSON (default: ./firebase-service-account.json)
export FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

### Firebase Console Setup
1. **Project**: bnb-blr-478413
2. **Authentication Methods**:
   - ✅ Email/Password
   - ✅ Google Sign-In
3. **Service Account**: Downloaded and saved as `firebase-service-account.json` (gitignored)

## Testing Locally

1. Start the server:
```bash
uv run uvicorn main:app --reload --port 8000
```

2. Open browser: http://127.0.0.1:8000

3. Test authentication flow:
   - Click "Login/Sign Up"
   - Try email signup: Create account with email/password
   - Try Google Sign-In: Click Google button
   - Upload files: Should require login
   - Chat: Should require login
   - Generate timetable: Should require login

4. Check browser console for Firebase SDK logs
5. Check terminal for backend auth verification logs

## Deployment to Google Cloud Run

### Update Dockerfile
The `firebase-service-account.json` needs to be available in the container:

```dockerfile
# Copy service account (ensure it's not in .dockerignore)
COPY firebase-service-account.json /app/firebase-service-account.json
```

### Deploy with Environment Variables
```bash
# Set environment variables
export GEMINI_API_KEY=AIzaSyBn5rbdGJa86yp0HtBxTaBrUKxHkdE0VFw
export FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json

# Build and deploy
gcloud builds submit --tag gcr.io/bnb-blr-478413/timetable-planner:latest .

gcloud run deploy timetable-planner \
  --image gcr.io/bnb-blr-478413/timetable-planner:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY,FIREBASE_SERVICE_ACCOUNT_PATH=$FIREBASE_SERVICE_ACCOUNT_PATH
```

### Alternative: Use Secret Manager
For better security, store credentials in Google Secret Manager:

```bash
# Create secret
gcloud secrets create firebase-service-account \
  --data-file=firebase-service-account.json

# Deploy with secret
gcloud run deploy timetable-planner \
  --image gcr.io/bnb-blr-478413/timetable-planner:latest \
  --update-secrets FIREBASE_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json=firebase-service-account:latest
```

## Security Features

1. **Token Verification**: All tokens validated with Firebase Admin SDK
2. **Rate Limiting**: 20 requests per minute per user
3. **User Isolation**: User UID tracked for rate limiting
4. **Secure Headers**: Bearer token authentication
5. **Context Guardrails**: AI validates chat context
6. **Protected Endpoints**: Only authenticated users can access key features

## API Response Examples

### Successful Authentication
```json
{
  "response": "✅ Timetable generated successfully!",
  "intent": {
    "timetable_data": {...}
  }
}
```

### Authentication Required
```json
{
  "detail": "Authentication required. Please log in.",
  "status_code": 401
}
```

### Rate Limited
```json
{
  "response": "⏱️ You're sending messages too quickly. Please wait a moment before trying again.",
  "intent": {"intent": "rate_limited"}
}
```

## Troubleshooting

### Firebase SDK Not Loading
- Check browser console for CORS errors
- Verify Firebase config in `firebase-config.js`
- Ensure Firebase SDK CDN is accessible

### Token Verification Fails
- Check `firebase-service-account.json` exists
- Verify service account has correct permissions
- Check logs: `INFO: Token verified for user: <uid>`

### Login Modal Doesn't Appear
- Check `auth.js` is loaded after `firebase-config.js`
- Verify `window.auth` is defined in console
- Check for JavaScript errors in console

### 401 Unauthorized Errors
- User not logged in - show login modal
- Token expired - re-authenticate user
- Invalid token - check Firebase console for user status

## Next Steps

1. **User Data Isolation**: Store timetables per user UID
2. **Role-Based Access**: Add admin/teacher/student roles
3. **Persistent Storage**: Move from in-memory to Firestore
4. **Email Verification**: Require verified emails
5. **Password Reset**: Add forgot password flow
6. **Multi-tenancy**: Support multiple universities

## Files Modified

✅ `static/index.html` - Added auth modal and user profile
✅ `static/firebase-config.js` - Firebase SDK initialization (NEW)
✅ `static/auth.css` - Authentication styling (NEW)
✅ `static/auth.js` - Auth logic and token management (NEW)
✅ `static/app.js` - Added auth headers to API calls
✅ `services/firebase_auth.py` - Backend token verification (NEW)
✅ `main.py` - Protected endpoints with @auth_required
✅ `requirements.txt` - Added firebase-admin, pyjwt
✅ `.gitignore` - Excluded firebase-service-account.json

## Authentication Flow

```
User Opens App
     ↓
Check Auth State (auth.js)
     ↓
Not Logged In? → Show Login Modal
     ↓
User Signs In (Email/Google)
     ↓
Get ID Token (getAuthToken)
     ↓
Send Request with Authorization Header
     ↓
Backend Verifies Token (firebase_auth.py)
     ↓
Extract User Info (uid, email)
     ↓
Process Request with User Context
     ↓
Return Response
```

## Success! 🎉

Firebase Authentication is now fully integrated. Users must sign in to:
- Chat with AI assistant
- Generate timetables
- Upload CSV/JSON files
- Access protected features

The system tracks users by Firebase UID for rate limiting and future user-specific data storage.
