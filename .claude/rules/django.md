---
paths: backend/**/*.py
---

# Django Development Rules

## Project Structure
- Use Django REST Framework for all API endpoints
- Organize apps by domain: members, bills, votes, finance, agent
- Keep views thin, business logic in services

## Models
- Use descriptive field names
- Add `created_at` and `updated_at` to all models
- Use UUIDs for public-facing IDs
- Document fields with help_text

## Views & Serializers
```python
# Use ViewSets for CRUD operations
class MemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'state']
```

## API Conventions
- Use consistent URL patterns: `/api/v1/members/`, `/api/v1/bills/`
- Return pagination for list endpoints
- Use proper HTTP status codes
- Include error details in responses

## MongoDB Integration
- Use Motor for async MongoDB operations
- Define schemas with Pydantic for validation
- Use aggregation pipelines for complex queries

## Testing
- Write tests for all API endpoints
- Use pytest-django
- Mock external API calls
- Test edge cases and error handling
