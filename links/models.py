"""
Django models for Shortify Link MVP.

Models:
    ShortLink: Represents a shortened URL mapping
    Click: Represents a click/visit event on a short link
"""

from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class ShortLink(models.Model):
    """
    Represents a shortened URL mapping.

    Attributes:
        original_url: The long URL to redirect to
        short_code: The generated short identifier (6-10 chars)
        created_at: Timestamp of link creation
        clicks_count: Denormalized count of clicks (updated by service)
    """

    id = models.BigAutoField(primary_key=True)
    original_url = models.URLField(max_length=2048, unique=True, db_index=True)
    short_code = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clicks_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "links_shortlink"
        ordering = ["-created_at"]
        verbose_name = "Short Link"
        verbose_name_plural = "Short Links"

    def __str__(self):
        """String representation showing short_code and truncated URL."""
        return f"{self.short_code} → {self.original_url[:50]}"

    def clean(self):
        """
        Validate URL has required protocol and is not localhost.

        Raises:
            ValidationError: If URL is invalid or localhost
        """
        if self.original_url:
            if not self.original_url.startswith(("http://", "https://")):
                raise ValidationError("URL must include http:// or https://")
            if "localhost" in self.original_url or "127.0.0.1" in self.original_url:
                raise ValidationError("Localhost URLs are not allowed")


class Click(models.Model):
    """
    Represents a single click/visit event on a short link.

    Attributes:
        short_link: Reference to the shortened link that was clicked
        clicked_at: Timestamp of the click event
        query_params: JSON object containing UTM and other URL parameters
        user_agent: Browser/device user agent string
        referrer: HTTP referrer header (where user came from)
        ip_address: Client IP address (IPv4 or IPv6)
    """

    id = models.BigAutoField(primary_key=True)
    short_link = models.ForeignKey(
        ShortLink, on_delete=models.CASCADE, related_name="clicks"
    )
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    query_params = models.JSONField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(max_length=2048, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "links_click"
        ordering = ["-clicked_at"]
        verbose_name = "Click"
        verbose_name_plural = "Clicks"
        indexes = [
            models.Index(fields=["clicked_at"]),
        ]

    def __str__(self):
        """String representation showing short_code and timestamp."""
        return f"Click on {self.short_link.short_code} at {self.clicked_at}"
