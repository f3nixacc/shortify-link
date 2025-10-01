"""
Service layer for Shortify Link business logic.

Services:
    LinkShortenerService: Handles link creation and deduplication
    ClickTrackerService: Handles click tracking and analytics
"""

import logging
from django.db import IntegrityError, transaction
from django.db.models import F
from django.core.exceptions import ValidationError

from .models import ShortLink, Click
from .utils import generate_short_code, validate_url

logger = logging.getLogger(__name__)


class LinkShortenerService:
    """
    Service for creating and managing shortened links.

    Implements URL deduplication and short code collision handling.
    """

    @staticmethod
    def create_link(original_url):
        """
        Create a shortened link with deduplication and collision retry.

        Args:
            original_url: The long URL to shorten

        Returns:
            ShortLink: The created or existing ShortLink instance

        Raises:
            ValidationError: If URL validation fails
            RuntimeError: If short code generation fails after max retries
        """
        try:
            # Validate URL format and constraints
            validate_url(original_url)

            # Check for existing link (deduplication - FR-002a)
            existing_link = ShortLink.objects.filter(
                original_url=original_url
            ).first()

            if existing_link:
                logger.info(
                    f"Returning existing short link: {existing_link.short_code} "
                    f"for URL: {original_url[:50]}"
                )
                return existing_link

            # Generate unique short code with collision retry
            max_retries = 10
            for attempt in range(max_retries):
                short_code = generate_short_code(length=6)

                try:
                    with transaction.atomic():
                        link = ShortLink.objects.create(
                            original_url=original_url,
                            short_code=short_code,
                        )
                        logger.info(
                            f"Created new short link: {short_code} "
                            f"for URL: {original_url[:50]}"
                        )
                        return link

                except IntegrityError as e:
                    # Short code collision - retry with new code
                    if "short_code" in str(e):
                        logger.warning(
                            f"Short code collision on attempt {attempt + 1}: "
                            f"{short_code}"
                        )
                        continue
                    else:
                        # Other integrity error (e.g., duplicate URL race condition)
                        raise

            # Max retries exhausted
            raise RuntimeError(
                f"Failed to generate unique short code after {max_retries} attempts"
            )

        except ValidationError as e:
            logger.error(f"URL validation failed for {original_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating link: {e}")
            raise


class ClickTrackerService:
    """
    Service for tracking clicks and updating analytics.

    Handles metadata extraction and atomic counter updates.
    """

    @staticmethod
    def record_click(short_link, request):
        """
        Record a click event with metadata and update click counter.

        Args:
            short_link: ShortLink instance that was clicked
            request: Django HttpRequest object with click metadata

        Returns:
            Click: The created Click instance

        Raises:
            Exception: If click recording fails (logged but not raised)
        """
        try:
            # Extract metadata from request
            metadata = ClickTrackerService._extract_metadata(request)

            with transaction.atomic():
                # Create click record
                click = Click.objects.create(
                    short_link=short_link,
                    query_params=metadata.get("query_params"),
                    user_agent=metadata.get("user_agent"),
                    referrer=metadata.get("referrer"),
                    ip_address=metadata.get("ip_address"),
                )

                # Atomically increment clicks_count using F() expression
                ShortLink.objects.filter(pk=short_link.pk).update(
                    clicks_count=F("clicks_count") + 1
                )

                logger.info(
                    f"Recorded click for {short_link.short_code} from "
                    f"IP {metadata.get('ip_address', 'unknown')}"
                )
                return click

        except Exception as e:
            logger.error(
                f"Failed to record click for {short_link.short_code}: {e}",
                exc_info=True,
            )
            # Don't raise - click tracking shouldn't break redirects
            return None

    @staticmethod
    def _extract_metadata(request):
        """
        Extract click metadata from HTTP request.

        Args:
            request: Django HttpRequest object

        Returns:
            dict: Metadata dictionary with query_params, user_agent, referrer, ip_address
        """
        metadata = {}

        # Extract query parameters (UTM params, etc.)
        if request.GET:
            metadata["query_params"] = dict(request.GET.items())

        # Extract user agent
        metadata["user_agent"] = request.META.get("HTTP_USER_AGENT")

        # Extract referrer
        metadata["referrer"] = request.META.get("HTTP_REFERER")

        # Extract IP address (FR-016a: capture full IP)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Get first IP in chain (original client IP)
            metadata["ip_address"] = x_forwarded_for.split(",")[0].strip()
        else:
            metadata["ip_address"] = request.META.get("REMOTE_ADDR")

        return metadata
