import os
from fastapi import Request, HTTPException
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth
import logging

logger = logging.getLogger(__name__)

# Load environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")
# Add base URL environment variables
BASE_URL = os.getenv("BASE_URL", "https://yourdomain.com")  # Default to your production URL

# Validate OAuth credentials
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("Google OAuth client ID and secret must be set in environment variables")

if not FACEBOOK_CLIENT_ID or not FACEBOOK_CLIENT_SECRET:
    raise RuntimeError("Facebook OAuth client ID and secret must be set in environment variables")

# Config for OAuth
config = Config(environ={
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
    "FACEBOOK_CLIENT_ID": FACEBOOK_CLIENT_ID,
    "FACEBOOK_CLIENT_SECRET": FACEBOOK_CLIENT_SECRET,
})

oauth = OAuth(config)

# Register Google OAuth
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Register Facebook OAuth
oauth.register(
    name='facebook',
    client_id=FACEBOOK_CLIENT_ID,
    client_secret=FACEBOOK_CLIENT_SECRET,
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email public_profile'},
)


# Google OAuth functions
async def google_oauth2_login(request: Request):
    """Initiate Google OAuth login"""
    # For Google, we can be more flexible
    if os.getenv("ENVIRONMENT") == "development":
        # Use the request's host in development for flexibility
        redirect_uri = request.url.replace(path="/auth/google/callback", query="")
    else:
        # Use hardcoded URL in production
        redirect_uri = f"{BASE_URL}/auth/google/callback"

    logger.info(f"Google OAuth login redirect URI: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def google_oauth2_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        if os.getenv("ENVIRONMENT") == "development":
            redirect_uri = request.url.replace(path="/auth/google/callback", query="")
        else:
            redirect_uri = f"{BASE_URL}/auth/google/callback"

        logger.info(f"Google OAuth callback redirect URI: {redirect_uri}")

        token = await oauth.google.authorize_access_token(request)
        logger.info("Successfully obtained Google access token")

        user_info = None
        try:
            user_info = await oauth.google.parse_id_token(request, token)
            logger.info("Successfully parsed Google ID token")
        except Exception as e:
            logger.warning(f"Failed to parse Google ID token: {e}, trying userinfo endpoint")
            try:
                resp = await oauth.google.get('https://www.googleapis.com/oauth2/v1/userinfo', token=token)
                user_info = resp.json()
                logger.info("Successfully got user info from Google userinfo endpoint")
            except Exception as userinfo_error:
                logger.error(f"Failed to get user info from Google userinfo endpoint: {userinfo_error}")
                raise HTTPException(status_code=500, detail="Failed to retrieve user information from Google")

        if not user_info or 'email' not in user_info:
            raise HTTPException(status_code=400, detail="Email not provided by Google")

        logger.info(f"Google user info: {user_info}")
        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Google OAuth login failed: {str(e)}")


# Facebook OAuth functions
async def facebook_oauth2_login(request: Request):
    """Initiate Facebook OAuth login"""
    # For Facebook, use a hardcoded URI that exactly matches what's in the Facebook Developer Console
    redirect_uri = f"{BASE_URL}/auth/facebook/callback"
    logger.info(f"Facebook OAuth login redirect URI: {redirect_uri}")
    return await oauth.facebook.authorize_redirect(request, redirect_uri)


async def facebook_oauth2_callback(request: Request):
    """Handle Facebook OAuth callback"""
    try:
        # Use the exact same hardcoded URI as in the login function
        redirect_uri = f"{BASE_URL}/auth/facebook/callback"
        logger.info(f"Facebook OAuth callback redirect URI: {redirect_uri}")

        token = await oauth.facebook.authorize_access_token(request)
        logger.info("Successfully obtained Facebook access token")

        # Get user info from Facebook Graph API
        resp = await oauth.facebook.get('me?fields=id,name,email,picture', token=token)
        user_info = resp.json()
        logger.info("Successfully got user info from Facebook")

        if not user_info.get('email'):
            # Facebook might not always provide email, so we use id as fallback
            logger.warning("Facebook did not provide email, using ID as identifier")
            user_info['email'] = f"facebook_{user_info['id']}@facebook.oauth"

        logger.info(f"Facebook user info: {user_info}")
        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook OAuth callback failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Facebook OAuth login failed: {str(e)}")