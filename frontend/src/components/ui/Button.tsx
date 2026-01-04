import { ButtonHTMLAttributes, ReactNode } from 'react'
import { clsx } from 'clsx'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'accent'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

export default function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2',
        {
          // Primary - Deep Indigo
          'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-md focus:ring-primary-500':
            variant === 'primary',

          // Secondary - Warm Slate
          'bg-slate-200 text-slate-800 hover:bg-slate-300 hover:shadow-sm focus:ring-slate-400':
            variant === 'secondary',

          // Outline - Slate Border
          'border-2 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 hover:shadow-sm focus:ring-slate-400':
            variant === 'outline',

          // Accent - Amber
          'bg-accent-500 text-white hover:bg-accent-600 hover:shadow-md focus:ring-accent-400':
            variant === 'accent',

          // Sizes
          'px-3 py-1.5 text-sm': size === 'sm',
          'px-5 py-2.5 text-base': size === 'md',
          'px-6 py-3 text-lg': size === 'lg',
        },
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
