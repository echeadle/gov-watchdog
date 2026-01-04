"""
Bill URL configuration.
"""

from django.urls import path

from bills.views import BillActionsView, BillDetailView, BillListView, BillSearchView

urlpatterns = [
    path("", BillListView.as_view(), name="bill-list"),
    path("search/", BillSearchView.as_view(), name="bill-search"),
    path("<str:bill_id>/", BillDetailView.as_view(), name="bill-detail"),
    path("<str:bill_id>/actions/", BillActionsView.as_view(), name="bill-actions"),
]
