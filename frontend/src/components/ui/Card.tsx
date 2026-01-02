import { ReactNode } from 'react'
import { clsx } from 'clsx'

interface CardProps {
  className?: string
  children: ReactNode
  onClick?: () => void
  hover?: boolean
}

export function Card({ className, children, onClick, hover = false }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-sm border border-gray-200',
        hover && 'cursor-pointer hover:shadow-md transition-shadow',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div className={clsx('px-4 py-3 border-b border-gray-100', className)}>
      {children}
    </div>
  )
}

export function CardBody({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={clsx('p-4', className)}>{children}</div>
}

export function CardFooter({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div className={clsx('px-4 py-3 border-t border-gray-100 bg-gray-50 rounded-b-lg', className)}>
      {children}
    </div>
  )
}
