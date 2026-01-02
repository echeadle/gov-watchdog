"""
Agent URL configuration.
"""

from django.urls import path

from agent.views import ChatView, ConversationView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="agent-chat"),
    path(
        "conversations/<str:conversation_id>/",
        ConversationView.as_view(),
        name="conversation-detail",
    ),
]
