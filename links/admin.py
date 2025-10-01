"""
Admin configuration for Shortify Link models.

Uses Unfold Admin for modern interface.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ShortLink, Click


@admin.register(ShortLink)
class ShortLinkAdmin(ModelAdmin):
    """
    Admin interface for ShortLink model with Unfold styling.
    """

    list_display = ["short_code", "original_url_truncated", "clicks_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["short_code", "original_url"]
    readonly_fields = ["short_code", "created_at", "clicks_count"]
    ordering = ["-created_at"]

    def original_url_truncated(self, obj):
        """
        Display truncated original URL in list view.

        Args:
            obj: ShortLink instance

        Returns:
            str: Truncated URL (max 60 chars)
        """
        return obj.original_url[:60] + "..." if len(obj.original_url) > 60 else obj.original_url

    original_url_truncated.short_description = "Original URL"


@admin.register(Click)
class ClickAdmin(ModelAdmin):
    """
    Admin interface for Click model with Unfold styling.
    """

    list_display = ["short_code_display", "clicked_at", "ip_address", "referrer_truncated"]
    list_filter = ["clicked_at", "short_link"]
    search_fields = ["short_link__short_code", "ip_address", "user_agent"]
    readonly_fields = ["short_link", "clicked_at", "query_params", "user_agent", "referrer", "ip_address"]
    ordering = ["-clicked_at"]

    def short_code_display(self, obj):
        """
        Display short code in list view.

        Args:
            obj: Click instance

        Returns:
            str: Short code from related ShortLink
        """
        return obj.short_link.short_code

    short_code_display.short_description = "Short Code"

    def referrer_truncated(self, obj):
        """
        Display truncated referrer in list view.

        Args:
            obj: Click instance

        Returns:
            str: Truncated referrer (max 50 chars) or empty string
        """
        if obj.referrer:
            return obj.referrer[:50] + "..." if len(obj.referrer) > 50 else obj.referrer
        return ""

    referrer_truncated.short_description = "Referrer"
