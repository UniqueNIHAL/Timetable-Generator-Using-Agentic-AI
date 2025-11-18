"""
Firebase Authentication Service
Handles token verification and user authentication
"""
import os
from functools import wraps
from typing import Optional
from fastapi import HTTPException, Request
import firebase_admin
from firebase_admin import credentials, auth
import logging

logger = logging.getLogger(__name__)

# Global flag to track if Firebase is available
_firebase_initialized = False

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    global _firebase_initialized
    
    try:
        # Check if already initialized
        if firebase_admin._apps:
            logger.info("Firebase already initialized")
            _firebase_initialized = True
            return True
        
        # Try environment variable first (for Cloud Run secret)
        firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')
        if firebase_credentials:
            import json
            cred_dict = json.loads(firebase_credentials)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully from environment variable")
            _firebase_initialized = True
            return True
        
        # Fall back to file path
        service_account_path = os.getenv(
            'FIREBASE_SERVICE_ACCOUNT_PATH', 
            'firebase-service-account.json'
        )
        
        if not os.path.exists(service_account_path):
            logger.warning(f"Firebase service account file not found: {service_account_path}")
            logger.warning("Firebase Authentication is DISABLED - all requests will be allowed")
            return False
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully from file")
        _firebase_initialized = True
        return True
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        logger.warning("Firebase Authentication is DISABLED due to initialization error")
        return False


def is_firebase_available():
    """Check if Firebase authentication is available"""
    return _firebase_initialized


def verify_firebase_token(id_token: str) -> Optional[dict]:
    """
    Verify Firebase ID token and return decoded token
    
    Args:
        id_token: Firebase ID token from client
        
    Returns:
        Decoded token with user information or None if invalid
    """
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(id_token)
        logger.info(f"Token verified for user: {decoded_token.get('uid')}")
        return decoded_token
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token")
        return None
    except auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase ID token")
        return None
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        return None


def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and verify user from request Authorization header
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information from decoded token or None
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            logger.warning("Invalid Authorization header format")
            return None
        
        token = parts[1]
        decoded_token = verify_firebase_token(token)
        
        if decoded_token:
            return {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name'),
                'email_verified': decoded_token.get('email_verified', False)
            }
        
        return None
    except Exception as e:
        logger.error(f"Error extracting user from request: {e}")
        return None


def auth_required(func):
    """
    Decorator to require authentication for endpoints
    Usage: @auth_required
    If Firebase is not available, allows all requests through
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Skip auth if Firebase is not initialized
        if not is_firebase_available():
            logger.warning("Firebase not available - allowing request without authentication")
            # Create a mock user for development
            request.state.user = {
                'uid': 'dev-user',
                'email': 'dev@example.com',
                'name': 'Development User',
                'email_verified': True
            }
            return await func(request, *args, **kwargs)
        
        user = get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please log in."
            )
        
        # Add user to request state for access in endpoint
        request.state.user = user
        
        return await func(request, *args, **kwargs)
    
    return wrapper


def optional_auth(func):
    """
    Decorator to optionally extract user info if authenticated
    Doesn't fail if no auth provided
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = get_current_user(request)
        request.state.user = user  # None if not authenticated
        return await func(request, *args, **kwargs)
    
    return wrapper
