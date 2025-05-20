from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import logging

from app.auth import create_access_token, get_password_hash, verify_password
from app.database import get_db
from app import models, schemas
from app.models import User
from app.utils import oauth_utils, email_utils

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_model=schemas.UserOut)
def register_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(password)
    db_user = models.User(email=email, hashed_password=hashed_password, role="user")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    email_utils.send_verification_email(db_user.email, db_user.id)
    return RedirectResponse("/login", status_code=303)


@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": db_user.email})

    response = RedirectResponse(
        url="/admin/dashboard" if db_user.role == "admin" else "/user/dashboard",
        status_code=303
    )
    response.set_cookie("access_token", access_token, httponly=True)
    return response


@router.get("/verify/{user_id}")
def verify_email(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.is_verified:
        return {"message": "Email already verified."}

    db_user.is_verified = True
    db.commit()
    db.refresh(db_user)

    return templates.TemplateResponse("verified.html", {"request": {}, "message": "Email verified successfully!"})


# Google OAuth Routes
@router.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    try:
        return await oauth_utils.google_oauth2_login(request)
    except Exception as e:
        logger.error(f"Error initiating Google login: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Google login")


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    return await handle_oauth_callback(request, db, oauth_utils.google_oauth2_callback, "Google")


# Facebook OAuth Routes
@router.get("/auth/facebook")
async def facebook_login(request: Request):
    """Initiate Facebook OAuth login"""
    try:
        return await oauth_utils.facebook_oauth2_login(request)
    except Exception as e:
        logger.error(f"Error initiating Facebook login: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate Facebook login")


@router.get("/auth/facebook/callback")
async def facebook_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Facebook OAuth callback"""
    return await handle_oauth_callback(request, db, oauth_utils.facebook_oauth2_callback, "Facebook")


# Common OAuth callback handler
async def handle_oauth_callback(request: Request, db: Session, callback_func, provider_name: str):
    """Common handler for OAuth callbacks"""
    try:
        # Get user info from OAuth provider
        user_info = await callback_func(request)
        email = user_info.get("email")

        if not email:
            logger.error(f"No email found in {provider_name} user info")
            raise HTTPException(status_code=400, detail=f"{provider_name} login failed: no email found")

        # Check if user exists, create if not
        db_user = db.query(User).filter(User.email == email).first()

        if not db_user:
            logger.info(f"Creating new user for email: {email} from {provider_name}")
            # Extract name if available
            name = user_info.get("name", email.split("@")[0])

            db_user = User(
                email=email,
                name=name if hasattr(User, 'name') else None,  # Only set if name field exists
                role="user",
                is_verified=True,
                hashed_password=None,  # No password for OAuth users
                oauth_provider=provider_name.lower()  # Track OAuth provider if field exists
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        else:
            logger.info(f"Existing user found: {email}")
            # Update OAuth provider if field exists
            if hasattr(db_user, 'oauth_provider') and not db_user.oauth_provider:
                db_user.oauth_provider = provider_name.lower()
                db.commit()

        # Create access token
        access_token = create_access_token(data={"sub": db_user.email})

        # Redirect to appropriate dashboard
        redirect_url = "/admin/dashboard" if db_user.role == "admin" else "/user/dashboard"
        response = RedirectResponse(url=redirect_url, status_code=303)

        # Set cookie with secure settings
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,  # 30 minutes
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )

        logger.info(f"Successfully authenticated user: {email} via {provider_name}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"{provider_name} OAuth callback error: {str(e)}", exc_info=True)
        # Redirect to login page with error message instead of raising exception
        return RedirectResponse(url=f"/login?error={provider_name.lower()}_oauth_failed", status_code=303)


@router.get("/logout")
def logout():
    """Logout endpoint that clears the access token cookie"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response