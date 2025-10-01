"""
Views for Shortify Link application.

Views:
    CreateLinkView: Handle link creation form submission
    RedirectView: Handle short code redirect with click tracking
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DeleteView, TemplateView
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count

from .models import ShortLink, Click
from .services import LinkShortenerService, ClickTrackerService
from .forms import LinkFilterForm

logger = logging.getLogger(__name__)


class CreateLinkView(View):
    """
    View for creating shortened links.

    GET: Display link creation form
    POST: Process link creation and display result
    """

    def get(self, request):
        """
        Display the link creation form.

        Args:
            request: Django HttpRequest object

        Returns:
            HttpResponse: Rendered template with form
        """
        return render(request, "links/create.html")

    def post(self, request):
        """
        Process link creation form submission.

        Args:
            request: Django HttpRequest object with original_url in POST data

        Returns:
            HttpResponse: Rendered template with created link or error
        """
        original_url = request.POST.get("original_url", "").strip()

        if not original_url:
            messages.error(request, "Please enter a URL to shorten.")
            return render(request, "links/create.html")

        try:
            # Use service layer for business logic
            short_link = LinkShortenerService.create_link(original_url)

            # Build short URL for display
            short_url = request.build_absolute_uri(f"/{short_link.short_code}")

            context = {
                "short_link": short_link,
                "short_url": short_url,
                "success": True,
            }
            return render(request, "links/create.html", context)

        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, "links/create.html", {"original_url": original_url})

        except Exception as e:
            logger.error(f"Error creating link: {e}", exc_info=True)
            messages.error(request, "An error occurred. Please try again.")
            return render(request, "links/create.html", {"original_url": original_url})


class RedirectView(View):
    """
    View for redirecting short codes with click tracking.

    Handles short code lookup, click tracking, and redirect with <200ms target.
    """

    def get(self, request, short_code):
        """
        Redirect short code to original URL with click tracking.

        Args:
            request: Django HttpRequest object
            short_code: The short code to redirect

        Returns:
            HttpResponse: 302 redirect to original URL or 404 if not found
        """
        # Lookup short link (raises 404 if not found)
        short_link = get_object_or_404(ShortLink, short_code=short_code)

        # Track click asynchronously (don't block redirect)
        try:
            ClickTrackerService.record_click(short_link, request)
        except Exception as e:
            # Log but don't fail redirect if tracking fails
            logger.error(f"Click tracking failed for {short_code}: {e}")

        # Redirect to original URL (FR-012a: <200ms target)
        return redirect(short_link.original_url, permanent=False)


class LinkListView(ListView):
    """
    View for listing all short links with filtering and sorting.

    GET: Display list with optional filters
    """

    model = ShortLink
    template_name = "links/list.html"
    context_object_name = "links"
    paginate_by = 20

    def get_queryset(self):
        """
        Get filtered and sorted queryset.

        Returns:
            QuerySet: Filtered ShortLink queryset
        """
        queryset = ShortLink.objects.all()

        # Get filter parameters
        search = self.request.GET.get("search", "").strip()
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        sort = self.request.GET.get("sort", "-created_at")

        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(original_url__icontains=search) | Q(short_code__icontains=search)
            )

        # Apply date filters
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        # Apply sorting
        if sort in ["-created_at", "created_at", "-clicks_count", "clicks_count"]:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        """
        Add filter form to context.

        Returns:
            dict: Context dictionary
        """
        context = super().get_context_data(**kwargs)
        context["filter_form"] = LinkFilterForm(self.request.GET or None)
        return context


class DeleteLinkView(DeleteView):
    """
    View for deleting a short link.

    POST: Delete link with CASCADE to clicks
    """

    model = ShortLink
    success_url = reverse_lazy("links:list")

    def delete(self, request, *args, **kwargs):
        """
        Delete short link and show success message.

        Returns:
            HttpResponse: Redirect to list view
        """
        short_link = self.get_object()
        logger.info(f"Deleting short link: {short_link.short_code}")
        messages.success(request, f"Short link '{short_link.short_code}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


class DashboardView(TemplateView):
    """
    View for analytics dashboard with aggregate statistics.

    GET: Display aggregate stats and click details
    """

    template_name = "links/dashboard.html"

    def get_context_data(self, **kwargs):
        """
        Calculate and return dashboard statistics.

        Returns:
            dict: Context with aggregate stats
        """
        context = super().get_context_data(**kwargs)

        # Get filter parameters
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        param_key = self.request.GET.get("param_key", "").strip()
        param_value = self.request.GET.get("param_value", "").strip()
        min_clicks = self.request.GET.get("min_clicks")

        # Base querysets
        links_qs = ShortLink.objects.all()
        clicks_qs = Click.objects.all()

        # Apply date filters to clicks
        if date_from:
            clicks_qs = clicks_qs.filter(clicked_at__gte=date_from)
        if date_to:
            clicks_qs = clicks_qs.filter(clicked_at__lte=date_to)

        # Apply param filter (search in JSON field)
        if param_key and param_value:
            clicks_qs = clicks_qs.filter(
                query_params__icontains=f'"{param_key}"'
            ).filter(
                query_params__icontains=f'"{param_value}"'
            )

        # Apply min_clicks filter
        if min_clicks:
            try:
                min_clicks_int = int(min_clicks)
                links_qs = links_qs.filter(clicks_count__gte=min_clicks_int)
            except ValueError:
                pass

        # Calculate aggregate stats
        total_links = links_qs.count()
        total_clicks = clicks_qs.count()

        # Get top links by clicks
        top_links = links_qs.order_by("-clicks_count")[:10]

        # Get recent clicks with metadata
        recent_clicks = clicks_qs.select_related("short_link").order_by("-clicked_at")[:50]

        context.update({
            "total_links": total_links,
            "total_clicks": total_clicks,
            "top_links": top_links,
            "recent_clicks": recent_clicks,
            "date_from": date_from or "",
            "date_to": date_to or "",
            "param_key": param_key,
            "param_value": param_value,
            "min_clicks": min_clicks or "",
        })

        return context
