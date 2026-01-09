import { Component, ErrorInfo, ReactNode } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Filter out extension-related errors
    const errorMessage = error.message || String(error)
    const isExtensionError = 
      errorMessage.includes('[PHANTOM]') ||
      errorMessage.includes('moz-extension://') ||
      errorMessage.includes('chrome-extension://') ||
      errorMessage.includes('Could not establish connection') ||
      errorMessage.includes('Receiving end does not exist')
    
    // Only log non-extension errors
    if (!isExtensionError) {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-gradient-subtle flex items-center justify-center p-6">
          <Alert className="max-w-md" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Something went wrong</AlertTitle>
            <AlertDescription className="mt-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </AlertDescription>
            <Button
              onClick={this.handleReset}
              className="mt-4"
              variant="outline"
            >
              Try again
            </Button>
          </Alert>
        </div>
      )
    }

    return this.props.children
  }
}
