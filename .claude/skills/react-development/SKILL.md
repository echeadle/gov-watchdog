---
name: react-development
description: React and Vite development patterns. Use when building components, hooks, pages, or configuring the frontend build.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# React Development Skill

## Project Setup

### Initialize Vite + React + TypeScript
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install axios react-router-dom @tanstack/react-query tailwindcss postcss autoprefixer

# Initialize Tailwind
npx tailwindcss init -p
```

### Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Base UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Input.tsx
│   │   ├── layout/          # Layout components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Layout.tsx
│   │   └── features/        # Feature components
│   │       ├── MemberCard.tsx
│   │       ├── BillList.tsx
│   │       └── VotingChart.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Members.tsx
│   │   ├── MemberDetail.tsx
│   │   ├── Bills.tsx
│   │   └── Agent.tsx
│   ├── hooks/
│   │   ├── useMembers.ts
│   │   ├── useBills.ts
│   │   └── useAgent.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── memberService.ts
│   │   └── agentService.ts
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── tailwind.config.js
└── vite.config.ts
```

## Configuration Files

### tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
```

### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## Type Definitions

### src/types/index.ts
```typescript
export interface Member {
  bioguide_id: string;
  name: string;
  first_name: string;
  last_name: string;
  party: 'D' | 'R' | 'I';
  state: string;
  district?: number;
  chamber: 'house' | 'senate';
  image_url?: string;
}

export interface Bill {
  bill_id: string;
  title: string;
  short_title?: string;
  sponsor_id: string;
  status: string;
  introduced_date: string;
}

export interface Vote {
  vote_id: string;
  question: string;
  result: string;
  date: string;
  yea: number;
  nay: number;
}

export interface AgentMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

## Component Patterns

### UI Component: Button
```typescript
// src/components/ui/Button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = ({
  variant = 'primary',
  size = 'md',
  isLoading,
  children,
  className,
  ...props
}: ButtonProps) => {
  const baseStyles = 'rounded-lg font-medium transition-colors';

  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    ghost: 'text-gray-600 hover:bg-gray-100',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={isLoading}
      {...props}
    >
      {isLoading ? 'Loading...' : children}
    </button>
  );
};
```

### Feature Component: MemberCard
```typescript
// src/components/features/MemberCard.tsx
import { Member } from '@/types';
import { Link } from 'react-router-dom';

interface MemberCardProps {
  member: Member;
}

export const MemberCard = ({ member }: MemberCardProps) => {
  const partyColors = {
    D: 'bg-blue-100 text-blue-800',
    R: 'bg-red-100 text-red-800',
    I: 'bg-gray-100 text-gray-800',
  };

  return (
    <Link
      to={`/members/${member.bioguide_id}`}
      className="block p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
    >
      <div className="flex items-center gap-4">
        {member.image_url && (
          <img
            src={member.image_url}
            alt={member.name}
            className="w-16 h-16 rounded-full object-cover"
          />
        )}
        <div>
          <h3 className="font-semibold text-lg">{member.name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`px-2 py-0.5 rounded text-sm ${partyColors[member.party]}`}>
              {member.party}
            </span>
            <span className="text-gray-600">
              {member.state}{member.district ? `-${member.district}` : ''}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
};
```

## Custom Hooks

### useMembers Hook
```typescript
// src/hooks/useMembers.ts
import { useQuery } from '@tanstack/react-query';
import { memberService } from '@/services/memberService';

interface UseMembersOptions {
  state?: string;
  chamber?: string;
  query?: string;
}

export const useMembers = (options: UseMembersOptions = {}) => {
  return useQuery({
    queryKey: ['members', options],
    queryFn: () => memberService.search(options),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useMember = (bioguideId: string) => {
  return useQuery({
    queryKey: ['member', bioguideId],
    queryFn: () => memberService.getById(bioguideId),
    enabled: !!bioguideId,
  });
};
```

## Service Layer

### API Client
```typescript
// src/services/api.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### Member Service
```typescript
// src/services/memberService.ts
import { api } from './api';
import { Member } from '@/types';

interface SearchParams {
  state?: string;
  chamber?: string;
  query?: string;
}

export const memberService = {
  search: async (params: SearchParams): Promise<Member[]> => {
    const { data } = await api.get('/members/', { params });
    return data.results;
  },

  getById: async (bioguideId: string): Promise<Member> => {
    const { data } = await api.get(`/members/${bioguideId}/`);
    return data;
  },
};
```

## App Setup

### main.tsx
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
```

## Common Commands
```bash
# Development
npm run dev

# Build
npm run build

# Preview production build
npm run preview

# Type checking
npm run typecheck

# Linting
npm run lint
```
