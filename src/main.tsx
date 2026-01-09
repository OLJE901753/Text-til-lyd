import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Filter out browser extension errors from console
// This prevents Phantom wallet and other extension errors from cluttering the console
const originalError = console.error
const originalWarn = console.warn

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
const originalLog = console.log
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

// Handle unhandled promise rejections from extensions
window.addEventListener('unhandledrejection', (event) => {
  const errorMessage = event.reason?.message || String(event.reason || '')
  
  // Suppress extension-related promise rejections
  if (
    errorMessage.includes('[PHANTOM]') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('Could not establish connection')
  ) {
    event.preventDefault()
    return
  }
})

// Handle general errors from extensions
window.addEventListener('error', (event) => {
  const errorMessage = event.message || String(event.error || '')
  const source = event.filename || ''
  
  // Suppress extension-related errors
  if (
    errorMessage.includes('[PHANTOM]') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('Could not establish connection') ||
    errorMessage.includes('Receiving end does not exist') ||
    source.includes('moz-extension://') ||
    source.includes('chrome-extension://')
  ) {
    event.preventDefault()
    return
  }
}, true)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
