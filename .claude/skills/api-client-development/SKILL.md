---
name: api-client-development
description: Building API client wrappers and integrations. Use when creating clients for Congress.gov, FEC, or other external APIs.
allowed-tools: Read, Write, Edit, Bash, WebFetch
---

# API Client Development Skill

## Base Client Pattern

### Async HTTP Client
```python
# backend/clients/base.py
import httpx
import asyncio
from typing import Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: Any = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)

class RateLimitError(APIError):
    pass

def retry_on_rate_limit(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except RateLimitError:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s...")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

class BaseAPIClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client

    def _get_headers(self) -> dict:
        return {}

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry_on_rate_limit()
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> dict:
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(429, "Rate limit exceeded")
            raise APIError(
                e.response.status_code,
                f"HTTP error: {e.response.status_code}",
                e.response.text,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Request failed: {str(e)}")

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: Optional[dict] = None) -> dict:
        return await self._request("POST", endpoint, json=json)
```

## Congress.gov API Client

```python
# backend/clients/congress.py
from .base import BaseAPIClient
from typing import List, Optional
from django.conf import settings

class CongressClient(BaseAPIClient):
    def __init__(self):
        super().__init__(
            base_url="https://api.congress.gov/v3",
            api_key=settings.CONGRESS_API_KEY,
        )

    def _get_headers(self) -> dict:
        return {"X-Api-Key": self.api_key}

    async def get_members(
        self,
        state: Optional[str] = None,
        chamber: Optional[str] = None,
        limit: int = 250,
        offset: int = 0,
    ) -> List[dict]:
        params = {"limit": limit, "offset": offset}
        if state:
            params["state"] = state

        endpoint = f"/member"
        if chamber:
            endpoint = f"/member/{chamber}"

        response = await self.get(endpoint, params=params)
        return response.get("members", [])

    async def get_member(self, bioguide_id: str) -> dict:
        response = await self.get(f"/member/{bioguide_id}")
        return response.get("member", {})

    async def get_member_bills(
        self,
        bioguide_id: str,
        bill_type: str = "sponsored",
        limit: int = 20,
    ) -> List[dict]:
        endpoint = f"/member/{bioguide_id}/{bill_type}-legislation"
        response = await self.get(endpoint, params={"limit": limit})
        return response.get("sponsoredLegislation", [])

    async def get_bill(self, congress: int, bill_type: str, number: int) -> dict:
        response = await self.get(f"/bill/{congress}/{bill_type}/{number}")
        return response.get("bill", {})

    async def get_bill_actions(self, congress: int, bill_type: str, number: int) -> List[dict]:
        response = await self.get(f"/bill/{congress}/{bill_type}/{number}/actions")
        return response.get("actions", [])

    async def get_votes(
        self,
        chamber: str,  # house or senate
        congress: int,
        session: int,
        limit: int = 20,
    ) -> List[dict]:
        endpoint = f"/{chamber}-vote"
        params = {"congress": congress, "session": session, "limit": limit}
        response = await self.get(endpoint, params=params)
        return response.get("votes", [])
```

## FEC API Client

```python
# backend/clients/fec.py
from .base import BaseAPIClient
from typing import List, Optional
from django.conf import settings

class FECClient(BaseAPIClient):
    def __init__(self):
        super().__init__(
            base_url="https://api.open.fec.gov/v1",
            api_key=settings.FEC_API_KEY,
        )

    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        params = params or {}
        params["api_key"] = self.api_key
        return await super().get(endpoint, params=params)

    async def search_candidates(
        self,
        name: Optional[str] = None,
        state: Optional[str] = None,
        office: Optional[str] = None,  # H, S, P
        cycle: Optional[int] = None,
        per_page: int = 20,
    ) -> List[dict]:
        params = {"per_page": per_page}
        if name:
            params["q"] = name
        if state:
            params["state"] = state
        if office:
            params["office"] = office
        if cycle:
            params["cycle"] = cycle

        response = await self.get("/candidates/search/", params=params)
        return response.get("results", [])

    async def get_candidate_totals(
        self,
        candidate_id: str,
        cycle: Optional[int] = None,
    ) -> dict:
        params = {}
        if cycle:
            params["cycle"] = cycle

        response = await self.get(f"/candidate/{candidate_id}/totals/", params=params)
        results = response.get("results", [])
        return results[0] if results else {}

    async def get_contributions(
        self,
        committee_id: str,
        min_amount: Optional[float] = None,
        per_page: int = 20,
    ) -> List[dict]:
        params = {"committee_id": committee_id, "per_page": per_page}
        if min_amount:
            params["min_amount"] = min_amount

        response = await self.get("/schedules/schedule_a/", params=params)
        return response.get("results", [])
```

## Caching Layer

```python
# backend/clients/cache.py
from typing import Any, Optional
import json
import hashlib
from datetime import timedelta
from config.database import mongodb

class APICache:
    def __init__(self, collection_name: str = "api_cache"):
        self.collection = mongodb.db[collection_name]

    def _make_key(self, prefix: str, params: dict) -> str:
        param_str = json.dumps(params, sort_keys=True)
        hash_val = hashlib.md5(param_str.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    async def get(self, prefix: str, params: dict) -> Optional[Any]:
        key = self._make_key(prefix, params)
        doc = await self.collection.find_one({"_id": key})

        if doc and doc.get("expires_at") > datetime.utcnow():
            return doc.get("data")
        return None

    async def set(
        self,
        prefix: str,
        params: dict,
        data: Any,
        ttl: timedelta = timedelta(hours=1),
    ):
        key = self._make_key(prefix, params)
        await self.collection.update_one(
            {"_id": key},
            {
                "$set": {
                    "data": data,
                    "expires_at": datetime.utcnow() + ttl,
                }
            },
            upsert=True,
        )

    async def invalidate(self, prefix: str):
        await self.collection.delete_many({"_id": {"$regex": f"^{prefix}:"}})
```

## Using Cached Client

```python
# backend/clients/congress_cached.py
from .congress import CongressClient
from .cache import APICache
from datetime import timedelta

class CachedCongressClient(CongressClient):
    def __init__(self):
        super().__init__()
        self.cache = APICache()

    async def get_member(self, bioguide_id: str) -> dict:
        cache_params = {"bioguide_id": bioguide_id}
        cached = await self.cache.get("member", cache_params)

        if cached:
            return cached

        data = await super().get_member(bioguide_id)
        await self.cache.set("member", cache_params, data, ttl=timedelta(hours=24))
        return data
```

## Client Usage
```python
# Example usage in service
from clients.congress_cached import CachedCongressClient

client = CachedCongressClient()

# In view or service
members = await client.get_members(state="CA")
member = await client.get_member("P000197")
bills = await client.get_member_bills("P000197", limit=10)

# Don't forget to close
await client.close()
```
