"""
Forms for Shortify Link application.

Forms:
    CreateShortLinkForm: Form for creating shortened links
    LinkFilterForm: Form for filtering links list
"""

from django import forms
from django.core.exceptions import ValidationError
from .utils import validate_url


class CreateShortLinkForm(forms.Form):
    """
    Form for creating a shortened link.

    Fields:
        original_url: The long URL to shorten
    """

    original_url = forms.URLField(
        max_length=2048,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com/your/long/url',
        }),
        label='URL to Shorten',
        help_text='Enter the full URL including http:// or https://'
    )

    def clean_original_url(self):
        """
        Validate the original URL.

        Returns:
            str: The validated URL

        Raises:
            ValidationError: If URL validation fails
        """
        url = self.cleaned_data.get('original_url')
        if url:
            try:
                validate_url(url)
            except ValidationError as e:
                raise ValidationError(str(e))
        return url


class LinkFilterForm(forms.Form):
    """
    Form for filtering the links list.

    Fields:
        search: Search term for URL or short code
        date_from: Filter links created after this date
        date_to: Filter links created before this date
        sort: Sort order
    """

    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('-clicks_count', 'Most Clicks'),
        ('clicks_count', 'Least Clicks'),
    ]

    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search URL or short code',
        }),
        label='Search'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='From Date'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='To Date'
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Sort By'
    )
