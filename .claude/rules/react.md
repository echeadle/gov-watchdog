---
paths: frontend/**/*.{tsx,jsx,ts,js}
---

# React Development Rules

## Component Structure
- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks
- Co-locate styles with components

## File Organization
```
src/
├── components/       # Reusable UI components
│   ├── ui/          # Base UI elements (Button, Card, Input)
│   └── features/    # Feature-specific components
├── pages/           # Route pages
├── hooks/           # Custom hooks
├── services/        # API clients
├── types/           # TypeScript types
└── utils/           # Helper functions
```

## State Management
- Use React Query for server state
- Use useState/useReducer for local state
- Avoid prop drilling - use context when needed

## Styling
- Use TailwindCSS for styling
- Follow mobile-first responsive design
- Use consistent spacing and colors

## TypeScript
- Define types for all props and API responses
- Use strict mode
- Avoid `any` type

## API Calls
```typescript
// Use React Query for data fetching
const { data, isLoading, error } = useQuery({
  queryKey: ['members', state],
  queryFn: () => memberService.getByState(state),
});
```

## Testing
- Use React Testing Library
- Test user interactions, not implementation
- Write integration tests for key flows
