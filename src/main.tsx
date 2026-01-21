import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { setupUnhandledRejectionHandler, setupErrorHandler } from './utils/errorHandler'

// Setup world-class error handling
setupUnhandledRejectionHandler()
setupErrorHandler()

// Filter out browser extension errors from console
// This prevents Phantom wallet and other extension errors from cluttering the console
const originalError = console.error
const originalWarn = console.warn
const originalLog = console.log

console.error = (...args: any[]) => {
  const errorMessage = args.join(' ')
  
  // Filter out known extension errors
  const shouldFilter = 
    errorMessage.includes('[PHANTOM]') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('Could not establish connection') ||
    errorMessage.includes('Receiving end does not exist') ||
    errorMessage.includes('solanaActionsContentScript') ||
    errorMessage.includes('contentScript.js')
  
  if (!shouldFilter) {
    originalError.apply(console, args)
  }
}

console.warn = (...args: any[]) => {
  const warningMessage = args.join(' ')
  
  // Filter out known extension warnings
  const shouldFilter = 
    warningMessage.includes('[PHANTOM]') ||
    warningMessage.includes('moz-extension://') ||
    warningMessage.includes('chrome-extension://')
  
  if (!shouldFilter) {
    originalWarn.apply(console, args)
  }
}

// Suppress CSS parsing errors from extensions
console.log = (...args: any[]) => {
  const logMessage = args.join(' ')
  
  // Filter out CSS parsing errors from extensions
  const shouldFilter = 
    logMessage.includes("Error in parsing value for '-webkit-text-size-adjust'") ||
    logMessage.includes('Declaration dropped')
  
  if (!shouldFilter) {
    originalLog.apply(console, args)
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
