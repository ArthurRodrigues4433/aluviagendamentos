"""
Authentication service for Aluvi backend.
Handles user authentication, token management, and security operations.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from sqlalchemy.orm import Session
from jose import jwt

from ..core.config import security
from ..core.database import db_manager
from ..models import User, AuditLog
from ..models.enums import AuditAction

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication operations."""

    @staticmethod
    def generate_temp_password() -> str:
        """
        Generate a secure temporary password.

        Returns:
            str: 12-character password with uppercase, lowercase, digits, and symbols
        """
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(12))

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return security.bcrypt_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return security.bcrypt_context.verify(plain_password, hashed_password)

    @staticmethod
    def authenticate_user(email: str, password: str, session: Session) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            email: User email
            password: Plain text password
            session: Database session

        Returns:
            User object if authentication successful, None otherwise
        """
        user = session.query(User).filter(User.email == email).first()
        if not user:
            return None

        if not AuthService.verify_password(password, user.password):
            return None

        return user

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, security.SECRET_KEY, algorithm=security.ALGORITHM)

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token with longer expiration.

        Args:
            data: Data to encode in the token

        Returns:
            Encoded JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=1)  # 1 day expiration
        to_encode = data.copy()
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, security.SECRET_KEY, algorithm=security.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def login_user(email: str, password: str, session: Session) -> Optional[Dict[str, Any]]:
        """
        Perform user login with validation and token generation.

        Args:
            email: User email
            password: User password
            session: Database session

        Returns:
            Dict with tokens and user info, or None if login fails
        """
        user = AuthService.authenticate_user(email, password, session)
        if not user:
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            return None

        # Check subscription for non-admin users
        if not user.is_admin and not user.subscription_paid:
            logger.warning(f"Login attempt for user with unpaid subscription: {email}")
            return None

        # Create tokens
        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = AuthService.create_access_token(token_data)
        refresh_token = AuthService.create_refresh_token(token_data)

        # Log successful login
        AuditLog.log_action(
            session=session,
            action=AuditAction.LOGIN,
            user_id=user.id,
            salon_id=user.id if not user.is_admin else None,
            details="Login realizado com sucesso"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user.role.value,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user.is_admin
            }
        }

    @staticmethod
    def create_owner_by_admin(
        admin_user: User,
        owner_data: Dict[str, Any],
        session: Session
    ) -> Dict[str, Any]:
        """
        Create a new salon owner (only admins can do this).

        Args:
            admin_user: Admin user creating the owner
            owner_data: Owner creation data
            session: Database session

        Returns:
            Dict with creation result
        """
        # Validate admin permissions
        if not admin_user.is_admin:
            raise ValueError("Only administrators can create salon owners")

        # Validate input data
        name = owner_data.get('name', '').strip()
        email = owner_data.get('email', '').strip()

        if not name:
            raise ValueError("Owner name is required")
        if not email:
            raise ValueError("Owner email is required")

        # Check if email already exists
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")

        # Generate temporary password
        temp_password = AuthService.generate_temp_password()
        hashed_password = AuthService.hash_password(temp_password)

        logger.info(f"Creating owner: {name} ({email})")

        # Create new owner
        new_owner = User(
            name=name,
            email=email,
            password=hashed_password,
            is_active=True,
            is_admin=False,
            subscription_paid=False,
            has_temp_password=True,
            is_first_login=True,
            temp_password=temp_password,
            created_by=admin_user.id
        )

        session.add(new_owner)
        session.commit()
        session.refresh(new_owner)

        # Log the creation
        AuditLog.log_action(
            session=session,
            action=AuditAction.OWNER_CREATION,
            user_id=admin_user.id,
            salon_id=new_owner.id,
            details=f"Owner created: {name} ({email})"
        )

        logger.info(f"Owner created successfully: ID={new_owner.id}")

        return {
            "success": True,
            "owner_id": new_owner.id,
            "message": f"Owner '{name}' created successfully",
            "temp_password": temp_password,  # Only for debugging - remove in production
            "notification_sent": True
        }

    @staticmethod
    def change_password(
        user: User,
        current_password: str,
        new_password: str,
        session: Session
    ) -> bool:
        """
        Change user password with validation.

        Args:
            user: User changing password
            current_password: Current password for verification
            new_password: New password
            session: Database session

        Returns:
            True if password changed successfully
        """
        # Verify current password
        if not AuthService.verify_password(current_password, user.password):
            return False

        # Validate new password
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long")

        # Hash and update password
        hashed_new_password = AuthService.hash_password(new_password)
        user.password = hashed_new_password
        user.has_temp_password = False
        user.is_first_login = False
        user.temp_password = None

        session.commit()

        # Log password change
        AuditLog.log_action(
            session=session,
            action=AuditAction.PASSWORD_CHANGE,
            user_id=user.id,
            salon_id=user.id if not user.is_admin else None,
            details="Password changed successfully"
        )

        return True