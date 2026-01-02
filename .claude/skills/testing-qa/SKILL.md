---
name: testing-qa
description: Testing strategies for Django and React. Use when writing unit tests, integration tests, or setting up test infrastructure.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Testing & QA Skill

## Backend Testing (Django + pytest)

### Setup
```bash
pip install pytest pytest-django pytest-asyncio httpx
```

### pytest.ini
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_test.py
asyncio_mode = auto
```

### Fixtures
```python
# backend/conftest.py
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from config.database import MongoDB

@pytest.fixture
async def mongodb():
    """Provide test database connection."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_gov_watchdog

    yield db

    # Cleanup after tests
    await client.drop_database("test_gov_watchdog")
    client.close()

@pytest.fixture
def api_client():
    """Provide test API client."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
async def sample_member(mongodb):
    """Create sample member for tests."""
    member = {
        "bioguide_id": "T000001",
        "name": "Test Member",
        "first_name": "Test",
        "last_name": "Member",
        "party": "D",
        "state": "CA",
        "district": 12,
        "chamber": "house",
    }
    await mongodb.members.insert_one(member)
    return member
```

### Unit Tests
```python
# backend/members/tests/test_services.py
import pytest
from members.services import MemberService

@pytest.mark.asyncio
async def test_search_members_by_state(mongodb, sample_member):
    service = MemberService(mongodb)

    results = await service.search(state="CA")

    assert len(results) == 1
    assert results[0]["bioguide_id"] == "T000001"

@pytest.mark.asyncio
async def test_search_members_empty_result(mongodb):
    service = MemberService(mongodb)

    results = await service.search(state="XX")

    assert len(results) == 0

@pytest.mark.asyncio
async def test_get_member_by_id(mongodb, sample_member):
    service = MemberService(mongodb)

    member = await service.get_by_id("T000001")

    assert member is not None
    assert member["name"] == "Test Member"

@pytest.mark.asyncio
async def test_get_member_not_found(mongodb):
    service = MemberService(mongodb)

    member = await service.get_by_id("INVALID")

    assert member is None
```

### API Tests
```python
# backend/members/tests/test_views.py
import pytest
from rest_framework import status

@pytest.mark.asyncio
async def test_member_list_endpoint(api_client, sample_member):
    response = api_client.get('/api/v1/members/')

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.json()

@pytest.mark.asyncio
async def test_member_list_filter_by_state(api_client, sample_member):
    response = api_client.get('/api/v1/members/?state=CA')

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(m['state'] == 'CA' for m in data['results'])

@pytest.mark.asyncio
async def test_member_detail_endpoint(api_client, sample_member):
    response = api_client.get('/api/v1/members/T000001/')

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == "Test Member"

@pytest.mark.asyncio
async def test_member_not_found(api_client):
    response = api_client.get('/api/v1/members/INVALID/')

    assert response.status_code == status.HTTP_404_NOT_FOUND
```

### Mocking External APIs
```python
# backend/tests/test_api_clients.py
import pytest
from unittest.mock import AsyncMock, patch
from clients.congress import CongressClient

@pytest.mark.asyncio
async def test_fetch_members_from_api():
    mock_response = {
        "members": [
            {"bioguideId": "A000001", "name": "Test Person"}
        ]
    }

    with patch.object(CongressClient, '_fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_response

        client = CongressClient()
        result = await client.get_members(state="CA")

        assert len(result) == 1
        mock_fetch.assert_called_once()
```

## Frontend Testing (Vitest + React Testing Library)

### Setup
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### vite.config.ts (Test Config)
```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'src/test/'],
    },
  },
});
```

### Test Setup
```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock fetch globally
global.fetch = vi.fn();

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks();
});
```

### Component Tests
```typescript
// src/components/features/__tests__/MemberCard.test.tsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MemberCard } from '../MemberCard';

const mockMember = {
  bioguide_id: 'T000001',
  name: 'Test Member',
  first_name: 'Test',
  last_name: 'Member',
  party: 'D' as const,
  state: 'CA',
  district: 12,
  chamber: 'house' as const,
};

const renderWithRouter = (component: React.ReactNode) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('MemberCard', () => {
  it('renders member name', () => {
    renderWithRouter(<MemberCard member={mockMember} />);

    expect(screen.getByText('Test Member')).toBeInTheDocument();
  });

  it('displays party affiliation', () => {
    renderWithRouter(<MemberCard member={mockMember} />);

    expect(screen.getByText('D')).toBeInTheDocument();
  });

  it('shows state and district', () => {
    renderWithRouter(<MemberCard member={mockMember} />);

    expect(screen.getByText('CA-12')).toBeInTheDocument();
  });

  it('links to member detail page', () => {
    renderWithRouter(<MemberCard member={mockMember} />);

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/members/T000001');
  });
});
```

### Hook Tests
```typescript
// src/hooks/__tests__/useMembers.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMembers } from '../useMembers';
import { vi } from 'vitest';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useMembers', () => {
  it('fetches members successfully', async () => {
    const mockMembers = [{ bioguide_id: 'T000001', name: 'Test' }];

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ results: mockMembers }),
    } as Response);

    const { result } = renderHook(() => useMembers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockMembers);
  });

  it('handles errors', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('API Error'));

    const { result } = renderHook(() => useMembers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
```

## Test Commands

```bash
# Backend
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest --cov=.                   # With coverage
pytest -k "test_member"          # Run specific tests
pytest -x                        # Stop on first failure

# Frontend
npm test                         # Run tests
npm run test:watch               # Watch mode
npm run test:coverage            # With coverage
npm run test:ui                  # UI mode
```

## Coverage Goals
- Backend: 80% coverage minimum
- Frontend: 70% coverage minimum
- Critical paths: 100% coverage
