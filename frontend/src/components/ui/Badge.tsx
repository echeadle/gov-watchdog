import { ReactNode } from 'react'
import { clsx } from 'clsx'

interface BadgeProps {
  variant?:
    | 'default'
    | 'primary'
    | 'accent'
    | 'info'
    | 'democratic'
    | 'republican'
    | 'independent'
    | 'success'
    | 'warning'
    | 'error'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
  className?: string
}

export default function Badge({ variant = 'default', size = 'md', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-semibold rounded-full border',
        {
          // Theme Colors
          'bg-slate-100 text-slate-700 border-slate-200': variant === 'default',
          'bg-primary-100 text-primary-700 border-primary-200': variant === 'primary',
          'bg-accent-100 text-accent-700 border-accent-200': variant === 'accent',
          'bg-blue-100 text-blue-700 border-blue-200': variant === 'info',

          // Party Colors
          'bg-democratic text-white border-democratic': variant === 'democratic',
          'bg-republican text-white border-republican': variant === 'republican',
          'bg-independent text-white border-independent': variant === 'independent',

          // Status Colors
          'bg-green-100 text-green-700 border-green-200': variant === 'success',
          'bg-amber-100 text-amber-700 border-amber-200': variant === 'warning',
          'bg-red-100 text-red-700 border-red-200': variant === 'error',

          // Sizes
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-3 py-1 text-sm': size === 'md',
          'px-4 py-1.5 text-base': size === 'lg',
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
