"""
Vote API views.
"""

import logging

from django.http import JsonResponse
from django.views import View

from votes.services import VoteService

logger = logging.getLogger(__name__)


class VoteListView(View):
    """
    GET /api/v1/votes/
    Get recent votes.
    """

    async def get(self, request):
        try:
            chamber = request.GET.get("chamber")
            congress = int(request.GET.get("congress", 118))
            session = int(request.GET.get("session", 1))
            limit = int(request.GET.get("limit", 20))
            offset = int(request.GET.get("offset", 0))

            result = await VoteService.get_recent_votes(
                chamber=chamber,
                congress=congress,
                session=session,
                limit=limit,
                offset=offset,
            )

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("Error in VoteListView")
            return JsonResponse({"error": "Internal server error"}, status=500)


class VoteDetailView(View):
    """
    GET /api/v1/votes/{vote_id}/
    Get vote details.
    """

    async def get(self, request, vote_id: str):
        try:
            vote = await VoteService.get_vote(vote_id)
            if not vote:
                return JsonResponse(
                    {"error": f"Vote {vote_id} not found"}, status=404
                )
            return JsonResponse(vote)

        except Exception as e:
            logger.exception(f"Error fetching vote {vote_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)


class MemberVotesView(View):
    """
    GET /api/v1/members/{bioguide_id}/votes/
    Get a member's voting record.

    Note: This is mounted via members.urls but implemented here.
    """

    async def get(self, request, bioguide_id: str):
        try:
            chamber = request.GET.get("chamber")
            congress = int(request.GET.get("congress", 118))
            limit = int(request.GET.get("limit", 20))
            offset = int(request.GET.get("offset", 0))

            result = await VoteService.get_member_votes(
                bioguide_id=bioguide_id,
                chamber=chamber,
                congress=congress,
                limit=limit,
                offset=offset,
            )

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception(f"Error fetching votes for {bioguide_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)
