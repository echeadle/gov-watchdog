"""
Member API views.
"""

import logging
from typing import Optional

from django.http import JsonResponse
from django.views import View

from members.models import MemberSearchParams
from members.services import MemberService

logger = logging.getLogger(__name__)


class MemberListView(View):
    """
    GET /api/v1/members/
    List and search members.
    """

    async def get(self, request):
        try:
            # Parse query parameters
            params = MemberSearchParams(
                q=request.GET.get("q"),
                state=request.GET.get("state"),
                party=request.GET.get("party"),
                chamber=request.GET.get("chamber"),
                page=int(request.GET.get("page", 1)),
                page_size=int(request.GET.get("page_size", 20)),
            )

            result = await MemberService.search_members(params)
            return JsonResponse(result.model_dump())

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("Error in MemberListView")
            return JsonResponse({"error": "Internal server error"}, status=500)


class MemberDetailView(View):
    """
    GET /api/v1/members/{bioguide_id}/
    Get member details.
    """

    async def get(self, request, bioguide_id: str):
        try:
            member = await MemberService.get_member(bioguide_id)
            if not member:
                return JsonResponse(
                    {"error": f"Member {bioguide_id} not found"}, status=404
                )
            return JsonResponse(member)

        except Exception as e:
            logger.exception(f"Error fetching member {bioguide_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)


class MemberBillsView(View):
    """
    GET /api/v1/members/{bioguide_id}/bills/
    Get member's sponsored/cosponsored bills.
    """

    async def get(self, request, bioguide_id: str):
        try:
            bill_type = request.GET.get("type", "sponsored")
            if bill_type not in ("sponsored", "cosponsored"):
                return JsonResponse(
                    {"error": "type must be 'sponsored' or 'cosponsored'"}, status=400
                )

            limit = int(request.GET.get("limit", 20))
            offset = int(request.GET.get("offset", 0))

            result = await MemberService.get_member_bills(
                bioguide_id, bill_type=bill_type, limit=limit, offset=offset
            )

            if "error" in result:
                return JsonResponse(result, status=500)

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception(f"Error fetching bills for {bioguide_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)


class MemberAmendmentsView(View):
    """
    GET /api/v1/members/{bioguide_id}/amendments/
    Get member's sponsored amendments.
    """

    async def get(self, request, bioguide_id: str):
        try:
            limit = int(request.GET.get("limit", 20))
            offset = int(request.GET.get("offset", 0))

            result = await MemberService.get_member_amendments(
                bioguide_id, limit=limit, offset=offset
            )

            if "error" in result:
                return JsonResponse(result, status=500)

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception(f"Error fetching amendments for {bioguide_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)


class MemberStatsView(View):
    """
    GET /api/v1/members/stats/
    Get aggregate member statistics.
    """

    async def get(self, request):
        try:
            stats = await MemberService.get_member_stats()
            return JsonResponse(stats)
        except Exception as e:
            logger.exception("Error fetching member stats")
            return JsonResponse({"error": "Internal server error"}, status=500)


class StatesView(View):
    """
    GET /api/v1/members/states/
    Get list of states with member counts.
    """

    async def get(self, request):
        try:
            states = await MemberService.get_states_with_members()
            return JsonResponse({"states": states})
        except Exception as e:
            logger.exception("Error fetching states")
            return JsonResponse({"error": "Internal server error"}, status=500)
