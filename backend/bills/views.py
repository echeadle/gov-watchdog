"""
Bill API views.
"""

import logging

from django.http import JsonResponse
from django.views import View

from bills.services import BillService

logger = logging.getLogger(__name__)


class BillListView(View):
    """
    GET /api/v1/bills/
    Search bills in local database.
    """

    async def get(self, request):
        try:
            congress = request.GET.get("congress")
            bill_type = request.GET.get("type")
            sponsor_id = request.GET.get("sponsor_id")
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))

            result = await BillService.search_bills(
                congress=int(congress) if congress else None,
                bill_type=bill_type,
                sponsor_id=sponsor_id,
                page=page,
                page_size=page_size,
            )

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("Error in BillListView")
            return JsonResponse({"error": "Internal server error"}, status=500)


class BillDetailView(View):
    """
    GET /api/v1/bills/{bill_id}/
    Get bill details.
    """

    async def get(self, request, bill_id: str):
        try:
            bill = await BillService.get_bill(bill_id)
            if not bill:
                return JsonResponse(
                    {"error": f"Bill {bill_id} not found"}, status=404
                )
            return JsonResponse(bill)

        except Exception as e:
            logger.exception(f"Error fetching bill {bill_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)


class BillActionsView(View):
    """
    GET /api/v1/bills/{bill_id}/actions/
    Get bill actions/history.
    """

    async def get(self, request, bill_id: str):
        try:
            limit = int(request.GET.get("limit", 20))
            result = await BillService.get_bill_actions(bill_id, limit=limit)

            if "error" in result and not result.get("results"):
                return JsonResponse(result, status=500)

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception(f"Error fetching actions for {bill_id}")
            return JsonResponse({"error": "Internal server error"}, status=500)


class BillSearchView(View):
    """
    GET /api/v1/bills/search/

    Search bills with keyword, party, subject, and congress filters.

    Query params:
    - q: str (keyword search on title and summaries)
    - party: str (D, R, I - filters by sponsor party)
    - subject: str (legislative subject name)
    - congress: int (119, 118, etc.)
    - page: int (default: 1)
    - page_size: int (default: 20)

    Example:
    GET /api/v1/bills/search/?q=climate&party=D&congress=119
    """

    async def get(self, request):
        try:
            # Extract query parameters
            query = request.GET.get("q")
            party = request.GET.get("party")
            subject = request.GET.get("subject")
            congress = request.GET.get("congress")
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 20))

            # Validate parameters
            if page < 1:
                return JsonResponse({"error": "Page must be >= 1"}, status=400)
            if page_size < 1 or page_size > 100:
                return JsonResponse(
                    {"error": "Page size must be between 1 and 100"}, status=400
                )

            # Execute search with incremental syncing
            result = await BillService.search_bills(
                query=query,
                party=party,
                subject=subject,
                congress=int(congress) if congress else None,
                page=page,
                page_size=page_size,
            )

            return JsonResponse(result)

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.exception("Error in BillSearchView")
            return JsonResponse({"error": "Internal server error"}, status=500)
