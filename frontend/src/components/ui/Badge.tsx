import { ReactNode } from 'react'
import { clsx } from 'clsx'

interface BadgeProps {
  variant?: 'default' | 'democratic' | 'republican' | 'independent' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'md'
  children: ReactNode
  className?: string
}

export default function Badge({ variant = 'default', size = 'md', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        {
          'bg-gray-100 text-gray-800': variant === 'default',
          'bg-democratic text-white': variant === 'democratic',
          'bg-republican text-white': variant === 'republican',
          'bg-independent text-white': variant === 'independent',
          'bg-green-100 text-green-800': variant === 'success',
          'bg-yellow-100 text-yellow-800': variant === 'warning',
          'bg-red-100 text-red-800': variant === 'error',
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-3 py-1 text-sm': size === 'md',
        },
        className
      )}
    >
      {children}
    </span>
  )
}

// Helper to get party badge variant
export function getPartyVariant(party: string): BadgeProps['variant'] {
  switch (party.toUpperCase()) {
    case 'D':
      return 'democratic'
    case 'R':
      return 'republican'
    case 'I':
      return 'independent'
    default:
      return 'default'
  }
}

// Helper to get full party name
export function getPartyName(party: string): string {
  switch (party.toUpperCase()) {
    case 'D':
      return 'Democrat'
    case 'R':
      return 'Republican'
    case 'I':
      return 'Independent'
    default:
      return party
  }
}
