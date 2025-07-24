# File: backend/main.py

import uuid
import logging

from datetime import timedelta
from typing import Optional
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import timedelta

logger = logging.getLogger(__name__)


from fastapi import FastAPI, Depends, HTTPException, Form, Request, Cookie

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode

from app.database import get_db
from app.models import User, Asset
from app.schemas import UserRead as UserSchema, LocationCreate as LocationCreate
from app.services.auth import (
    get_current_user,
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.services.audit_log import create_audit_log
from app.config import settings
from app.logging_config import setup_logging

from app.routers import users
from app.routers import suppliers
from app.routers import manufacturers
from app.routers import locations
from app.routers import areas
from app.routers import assets
from app.routers import asset_photos
from app.routers import asset_documents
from app.routers import asset_connections
from app.routers import global_connections
from app.routers import asset_interfaces
from app.routers import sites
from app.routers import tenants
from app.routers import locations_floormap
from app.routers import asset_types
from app.routers import dashboards
from app.routers import pcap
from app.routers import asset_statuses
from app.routers import contacts
from app.routers import audit_logs
from app.routers import roles
from app.routers import smtp_config
from app.routers import search
from app.routers import print as print_router
from app.routers import api_keys
from app.routers import external_api
from app.routers import setup
from app.setup_system import setup_system
from app.database import SessionLocal
from app.models import Tenant, User, Role

# Setup logging
setup_logging()

app = FastAPI(
    title="Industrace Multi-Tenant",
    description="Configuration Management Database for Industrial Control Systems",
    version="1.0.0",
    openapi_tags=[
        {"name": "assets", "description": "Industrial asset operations"},
        {"name": "external-api", "description": "Secure API for external integrations"},
        {"name": "api-keys", "description": "API Keys management for third parties"},
        {"name": "users", "description": "User management and authentication"},
        {"name": "tenants", "description": "Multi-tenant management"},
    ],
    docs_url="/docs" if settings.EXTERNAL_API_DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.EXTERNAL_API_DOCS_ENABLED else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenants.router, tags=["tenants"])
app.include_router(suppliers.router, tags=["suppliers"])
app.include_router(manufacturers.router, tags=["manufacturers"])
app.include_router(locations.router, tags=["locations"])
app.include_router(areas.router, tags=["areas"])
app.include_router(assets.router, tags=["assets"])
app.include_router(asset_photos.router, tags=["asset_photo"])
app.include_router(asset_documents.router, tags=["asset_document"])
app.include_router(asset_types.router, tags=["asset_type"])
app.include_router(sites.router, tags=["sites"])
app.include_router(asset_interfaces.router, tags=["asset_interfaces"])
app.include_router(asset_connections.router, tags=["asset_connection"])
app.include_router(global_connections.router, tags=["connections"])
app.include_router(locations_floormap.router, tags=["locations_floormap"])
app.include_router(users.router, tags=["users"])
app.include_router(dashboards.router, tags=["dashboards"])
app.include_router(pcap.router, tags=["pcap"])
app.include_router(asset_statuses.router, tags=["asset_statuses"])
app.include_router(contacts.router, tags=["contacts"])
app.include_router(audit_logs.router)
app.include_router(roles.router, tags=["roles"])
app.include_router(smtp_config.router, tags=["smtp-config"])
app.include_router(search.router, tags=["search"])
app.include_router(print_router.router, tags=["print"])
app.include_router(api_keys.router, tags=["api-keys"])
app.include_router(external_api.router, tags=["external-api"])
app.include_router(setup.router, tags=["setup"])


@app.on_event("startup")
async def startup_event():
    """Initializes the database if empty"""
    try:
        # Prima applica le migrazioni Alembic
        import subprocess
        import os
        
        print("Applying database migrations...")
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True)
            print("Database migrations applied successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error applying database migrations: {e}")
            # Continue anyway, it might be that the migrations are already applied
        
        db = SessionLocal()
        # Controlla se esistono tenant, utenti e ruoli
        tenant_count = db.query(Tenant).count()
        user_count = db.query(User).count()
        role_count = db.query(Role).count()
        
        if tenant_count == 0 and user_count == 0 and role_count == 0:
            print("Empty database detected. Automatic initialization...")
            setup_system()
            print("Database initialized successfully!")
            print("Default credentials:")
            print("  Admin: admin@example.com / admin123")
            print("  Editor: editor@example.com / editor123")
            print("  Viewer: viewer@example.com / viewer123")
        else:
            print(f"Database already configured (tenant: {tenant_count}, users: {user_count}, roles: {role_count})")
        
        db.close()
    except Exception as e:
        print(f"Error during database initialization: {e}")
        # Non blocchiamo l'avvio dell'app in caso di errore


from app.errors.validation_errors import ValidationError, InvalidVATNumberError, InvalidTaxCodeError, InvalidURLError, InvalidPhoneError, InvalidEmailError, InvalidIPAddressError, InvalidMACAddressError, InvalidVLANError, InvalidImpactValueError, InvalidPurdueLevelError, InvalidRiskScoreError, InvalidBusinessCriticalityError, InvalidRemoteAccessTypeError, InvalidPhysicalAccessEaseError, InvalidTenantSlugError, InvalidPasswordError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, validation_exc: RequestValidationError
):
    # Log the error for debugging (only in development)
    if settings.DEBUG:
        import builtins
        # builtins.print("Validation error:", validation_exc.errors)
        # builtins.print("Validation error details:")
        # for error in validation_exc.errors():
        #     builtins.print(f"  Field: {error['loc']}, Message: {error['msg']}, Type: {error['type']}")

    # Extract specific error messages
    validation_errors = []
    for error in validation_exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        
        # Handle our custom exceptions
        error_msg = error["msg"]
        # print(f"Processing error message: '{error_msg}'")
        
        # Extract the error code from the message
        if "INVALID_VAT_NUMBER" in error_msg:
            error_code = "INVALID_VAT_NUMBER"
        elif "INVALID_TAX_CODE" in error_msg:
            error_code = "INVALID_TAX_CODE"
        elif "INVALID_URL" in error_msg:
            error_code = "INVALID_URL"
        elif "INVALID_PHONE" in error_msg:
            error_code = "INVALID_PHONE"
        elif "INVALID_EMAIL" in error_msg:
            error_code = "INVALID_EMAIL"
        elif "INVALID_IP_ADDRESS" in error_msg:
            error_code = "INVALID_IP_ADDRESS"
        elif "INVALID_MAC_ADDRESS" in error_msg:
            error_code = "INVALID_MAC_ADDRESS"
        elif "INVALID_SERIAL_NUMBER" in error_msg:
            error_code = "INVALID_SERIAL_NUMBER"
        elif "INVALID_DATE" in error_msg:
            error_code = "INVALID_DATE"
        elif "INVALID_TIME" in error_msg:
            error_code = "INVALID_TIME"
        elif "INVALID_PORT" in error_msg:
            error_code = "INVALID_PORT"
        elif "INVALID_VLAN" in error_msg:
            error_code = "INVALID_VLAN"
        elif "INVALID_SUBNET_MASK" in error_msg:
            error_code = "INVALID_SUBNET_MASK"
        elif "INVALID_DEFAULT_GATEWAY" in error_msg:
            error_code = "INVALID_DEFAULT_GATEWAY"
        elif "INVALID_IMPACT_VALUE" in error_msg:
            error_code = "INVALID_IMPACT_VALUE"
        elif "INVALID_PURDUE_LEVEL" in error_msg:
            error_code = "INVALID_PURDUE_LEVEL"
        elif "INVALID_RISK_SCORE" in error_msg:
            error_code = "INVALID_RISK_SCORE"
        elif "INVALID_BUSINESS_CRITICALITY" in error_msg:
            error_code = "INVALID_BUSINESS_CRITICALITY"
        elif "INVALID_REMOTE_ACCESS_TYPE" in error_msg:
            error_code = "INVALID_REMOTE_ACCESS_TYPE"
        elif "INVALID_PHYSICAL_ACCESS_EASE" in error_msg:
            error_code = "INVALID_PHYSICAL_ACCESS_EASE"
        elif "INVALID_TENANT_SLUG" in error_msg:
            error_code = "INVALID_TENANT_SLUG"
        elif "INVALID_PASSWORD" in error_msg:
            error_code = "INVALID_PASSWORD"
        else:
            error_code = "VALIDATION_ERROR"
        
        validation_errors.append({
            "field": field,
            "error_code": error_code,
            "type": error["type"]
        })
    
    # Log the final response for debugging
    if settings.DEBUG:
        # print("Final response:", {
        #     "error_code": "VALIDATION_ERROR", 
        #     "detail": "Invalid input data",
        #     "validation_errors": validation_errors
        # })
        pass
    
    # Return the validation error details
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR", 
            "detail": "Invalid input data",
            "validation_errors": validation_errors
        },
    )


@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(
    request: Request, validation_exc: ValidationError
):
    # Log the error for debugging (only in development)
    if settings.DEBUG:
        import builtins
        # builtins.print(f"Custom validation error: {validation_exc.error_code} for field {validation_exc.field}")
        pass
    
    # Return the custom validation error
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "detail": "Invalid input data",
            "validation_errors": [{
                "field": validation_exc.field,
                "error_code": validation_exc.error_code,
                "type": "validation_error"
            }]
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"
        }
    )


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Industrace API", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    """Health check endpoint for monitoring"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# Auth endpoints
@app.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ErrorCodeException(status_code=401, error_code="INVALID_CREDENTIALS")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires,
    )

    # Audit log for login
    ip_address = request.client.host if request and request.client else None
    create_audit_log(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        action="login",
        entity="User",
        entity_id=user.id,
        description=f"User login {user.email}",
        ip_address=ip_address,
        commit=True,
    )

    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    # Secure cookie for frontend
    response.set_cookie(
        key="access_token_cookie",
        value=access_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE_COOKIES,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@app.post("/refresh")
async def refresh_token(
    access_token_cookie: Optional[str] = Cookie(None), db: Session = Depends(get_db)
):
    if not access_token_cookie:
        raise ErrorCodeException(status_code=401, error_code="UNEXISTENT_TOKEN")

    try:
        payload = jwt.decode(
            access_token_cookie,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        # Verify that the token is of the correct type
        token_type = payload.get("type")
        if token_type != "access":
            raise ErrorCodeException(status_code=401, error_code="INVALID_TOKEN_TYPE")

        if user_id is None or tenant_id is None:
            raise ErrorCodeException(status_code=401, error_code="INVALID_TOKEN")
    except ExpiredSignatureError:
        raise ErrorCodeException(status_code=401, error_code="EXPIRED_TOKEN")
    except JWTError:
        raise ErrorCodeException(status_code=401, error_code="INVALID_TOKEN")

    new_token = create_access_token(
        data={"sub": user_id, "tenant_id": tenant_id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = JSONResponse(content={"msg": "Token renewed"})
    response.set_cookie(
        key="access_token_cookie",
        value=new_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=settings.SAME_SITE_COOKIES,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@app.post("/logout")
async def logout(
    response: JSONResponse, 
    db: Session = Depends(get_db), 
    request: Request = None,
    access_token_cookie: Optional[str] = Cookie(None)
):
    response.delete_cookie("access_token_cookie", path="/")
    
    # Try to get current user for audit log, but don't fail if token is invalid
    current_user = None
    ip_address = request.client.host if request and request.client else None
    
    if access_token_cookie:
        try:
            # Decode token manually for logout audit
            payload = jwt.decode(
                access_token_cookie,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            if user_id:
                # Get user from database
                current_user = db.query(User).filter(User.id == user_id).first()
        except:
            # Token is invalid or expired, but we still want to log the logout attempt
            pass
    
    # Audit log for logout
    if current_user:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="logout",
            entity="User",
            entity_id=current_user.id,
            description=f"User logout {current_user.email}",
            ip_address=ip_address,
            commit=True,
        )
    else:
        # For anonymous logout, we can't create audit log since user_id is required
        # Just log to console for debugging
        logger.info(f"Anonymous logout attempt from IP: {ip_address}")
    
    return {"msg": "Logout successful"}


class ErrorCodeException(HTTPException):
    def __init__(self, status_code: int, error_code: str):
        self.error_code = error_code
        # Use error_code as detail for compatibility
        super().__init__(status_code=status_code, detail=error_code)


@app.exception_handler(ErrorCodeException)
async def error_code_exception_handler(request: Request, exc: ErrorCodeException):
    # Log the error for debugging (only in development)
    if settings.DEBUG:
        # print(f"ErrorCodeException: {exc.error_code} - {exc.status_code}")
        pass
    
    # Use the translations if available
    from app.errors.translations import messages
    from app.services.auth import get_current_user
    
    # Try to determine the language from the current user
    language = "en"  # default
    try:
        # Try to get the current user to determine the language
        # If it doesn't work, use the Accept-Language header
        accept_language = request.headers.get("accept-language", "en")
        if "it" in accept_language.lower():
            language = "it"
    except:
        pass
    
        # Get the translated message
    translated_message = messages.get(language, {}).get(exc.error_code, exc.error_code)
    
    return JSONResponse(
        status_code=exc.status_code, 
        content={"error_code": exc.error_code, "detail": translated_message}
    )


# Configure base logging
logging.basicConfig(level=logging.ERROR)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the error for debugging
    logging.error(f"Error 500 on {request.url}: {exc}", exc_info=True)
    
    # For the user, return only a generic message
    return JSONResponse(
        status_code=500, 
        content={"error_code": "INTERNAL_ERROR", "detail": "Errore interno del server"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
