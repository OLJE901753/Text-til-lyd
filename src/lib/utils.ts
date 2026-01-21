import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

/**
 * Checks if an error is from a browser extension (e.g., Phantom wallet)
 * This helps filter out extension-related errors that don't affect the app
 * @deprecated Use isExtensionError from '@/utils/errorHandler' instead
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