"""
Member URL configuration.
"""

from django.urls import path

from members.views import (
    MemberBillsView,
    MemberDetailView,
    MemberListView,
    MemberStatsView,
    StatesView,
)
from votes.views import MemberVotesView

urlpatterns = [
    path("", MemberListView.as_view(), name="member-list"),
    path("stats/", MemberStatsView.as_view(), name="member-stats"),
    path("states/", StatesView.as_view(), name="states-list"),
    path("<str:bioguide_id>/", MemberDetailView.as_view(), name="member-detail"),
    path("<str:bioguide_id>/bills/", MemberBillsView.as_view(), name="member-bills"),
    path("<str:bioguide_id>/votes/", MemberVotesView.as_view(), name="member-votes"),
]
