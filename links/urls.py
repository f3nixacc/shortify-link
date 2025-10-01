"""
URL configuration for links app.

Routes:
    / - CreateLinkView (link creation form)
    /links/ - LinkListView (list all links)
    /links/<id>/delete/ - DeleteLinkView (delete a link)
    /dashboard/ - DashboardView (analytics dashboard)
    /<short_code> - RedirectView (redirect to original URL)
"""

from django.urls import path
from .views import CreateLinkView, RedirectView, LinkListView, DeleteLinkView, DashboardView

app_name = "links"

urlpatterns = [
    path("", CreateLinkView.as_view(), name="create"),
    path("links/", LinkListView.as_view(), name="list"),
    path("links/<int:pk>/delete/", DeleteLinkView.as_view(), name="delete"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("<str:short_code>", RedirectView.as_view(), name="redirect"),
]
