import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingStateProps {
  message?: string
  variant?: 'default' | 'overlay' | 'inline'
  className?: string
}

export function LoadingState({
  message = 'Loading...',
  variant = 'default',
  className,
}: LoadingStateProps) {
  if (variant === 'overlay') {
    return (
      <div className={cn('fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm', className)}>
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </div>
      </div>
    )
  }

  if (variant === 'inline') {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('flex items-center justify-center p-8', className)}>
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        {message && <p className="text-sm text-muted-foreground">{message}</p>}
      </div>
    </div>
  )
}
