"""
Utility functions for Shortify Link.

Functions:
    generate_short_code: Generate a random URL-safe short code
    validate_url: Validate URL format and constraints
"""

import secrets
import string
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def generate_short_code(length=6):
    """
    Generate a random URL-safe short code.

    Args:
        length: Length of the short code (default 6 characters)

    Returns:
        str: Random alphanumeric string (a-zA-Z0-9)
    """
    alphabet = string.ascii_letters + string.digits  # a-zA-Z0-9
    return "".join(secrets.choice(alphabet) for _ in range(length))


def validate_url(url):
    """
    Validate URL format and check constraints.

    Args:
        url: URL string to validate

    Returns:
        bool: True if URL is valid

    Raises:
        ValidationError: If URL is invalid, missing protocol, or is localhost
    """
    # Check protocol
    if not url.startswith(("http://", "https://")):
        raise ValidationError("URL must include http:// or https://")

    # Check for localhost
    if "localhost" in url.lower() or "127.0.0.1" in url:
        raise ValidationError("Localhost URLs are not allowed")

    # Validate URL format
    validator = URLValidator()
    validator(url)  # Raises ValidationError if invalid

    return True
