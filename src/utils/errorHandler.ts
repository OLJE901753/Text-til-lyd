/**
 * World-class error handling utilities
 * Provides robust error handling and logging
 */

export interface ErrorInfo {
  message: string
  stack?: string
  componentStack?: string
  timestamp: string
  userAgent: string
  url: string
}

/**
 * Logs errors to console with proper formatting
 */
export function logError(error: Error, errorInfo?: { componentStack?: string }): void {
  const errorData: ErrorInfo = {
    message: error.message,
    stack: error.stack,
    componentStack: errorInfo?.componentStack,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
  }

  // Only log non-extension errors
  if (!isExtensionError(error)) {
    console.error('Application Error:', errorData)
    
    // In production, you could send this to an error tracking service
    // Example: Sentry.captureException(error, { extra: errorData })
  }
}

/**
 * Checks if an error is from a browser extension
 */
export function isExtensionError(error: Error | string | unknown): boolean {
  const errorMessage = typeof error === 'string' 
    ? error 
    : error instanceof Error 
    ? error.message 
    : String(error || '')
  
  return (
    errorMessage.includes('[PHANTOM]') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('Could not establish connection') ||
    errorMessage.includes('Receiving end does not exist') ||
    errorMessage.includes('solanaActionsContentScript') ||
    errorMessage.includes('contentScript.js')
  )
}

/**
 * Handles unhandled promise rejections
 */
export function setupUnhandledRejectionHandler(): void {
  window.addEventListener('unhandledrejection', (event) => {
    const errorMessage = event.reason?.message || String(event.reason || '')
    
    if (isExtensionError(errorMessage)) {
      event.preventDefault()
      return
    }
    
    // Log legitimate errors
    console.error('Unhandled Promise Rejection:', event.reason)
  })
}

/**
 * Handles general window errors
 */
export function setupErrorHandler(): void {
  window.addEventListener('error', (event) => {
    const errorMessage = event.message || String(event.error || '')
    const source = event.filename || ''
    
    if (isExtensionError(errorMessage) || source.includes('moz-extension://') || source.includes('chrome-extension://')) {
      event.preventDefault()
      return
    }
    
    // Log legitimate errors
    if (event.error) {
      logError(event.error)
    }
  }, true)
}
