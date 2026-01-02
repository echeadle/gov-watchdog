"""
Vote URL configuration.
"""

from django.urls import path

from votes.views import VoteDetailView, VoteListView

urlpatterns = [
    path("", VoteListView.as_view(), name="vote-list"),
    path("<str:vote_id>/", VoteDetailView.as_view(), name="vote-detail"),
]
