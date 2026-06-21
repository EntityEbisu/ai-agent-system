"""Unit tests for JWT handler and auth dependencies."""
import os
import time
from unittest.mock import patch

import jwt
import pytest

from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.dependencies import verify_token

# Ensure a test secret key is available
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


class TestJWTHandler:
    def test_create_token(self):
        token = create_access_token(user_id="test-user")
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        token = create_access_token(user_id="demo")
        payload = decode_access_token(token)
        assert payload["sub"] == "demo"
        assert "iat" in payload
        assert "exp" in payload

    def test_decode_invalid_token_raises(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("invalid.token.here")
