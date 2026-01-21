import axios, { AxiosInstance, AxiosError } from 'axios'
import { TranscriptionResponse, ErrorResponse, HealthResponse } from '@/types'
import { API_BASE_URL } from './constants'

class ApiClient {
  private client: AxiosInstance
  private retryCount = 3
  private retryDelay = 1000

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 3600000, // 60 minutes (1 hour) for very large files (75MB+ can take 45-60+ minutes on CPU)
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const config = error.config as any

        // Don't retry if already retried or if it's a non-retryable error
        if (
          !config ||
          config.__retryCount >= this.retryCount ||
          !this.isRetryableError(error)
        ) {
          return Promise.reject(this.transformError(error))
        }

        config.__retryCount = config.__retryCount || 0
        config.__retryCount += 1

        // Exponential backoff
        const delay = this.retryDelay * Math.pow(2, config.__retryCount - 1)
        await new Promise((resolve) => setTimeout(resolve, delay))

        return this.client(config)
      }
    )
  }

  private isRetryableError(error: AxiosError): boolean {
    if (!error.response) {
      // Network error - retry only if it's a connection issue, not timeout
      // Timeouts shouldn't be retried immediately as they indicate the request is too long
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return false // Don't retry timeouts
      }
      // Retry connection errors (network issues)
      return true
    }

    const status = error.response.status
    // Retry on 5xx errors (server errors) and 429 (rate limit)
    // Don't retry 4xx errors (client errors) or 504 (gateway timeout - already timed out)
    return (status >= 500 && status !== 504) || status === 429
  }

  private transformError(error: AxiosError): ErrorResponse {
    if (error.response) {
      const data = error.response.data as ErrorResponse
      return {
        error: data.error || 'An error occurred',
        detail: data.detail || error.message,
        code: data.code || `HTTP_${error.response.status}`,
      }
    }

    if (error.request) {
      // Check if it's a timeout error
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return {
          error: 'Timeout error',
          detail: 'The request timed out. The file may be too large or the server is overloaded.',
          code: 'TIMEOUT_ERROR',
        }
      }
      
      // Check if it's a network/connection error
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED' || !navigator.onLine) {
        return {
          error: 'Network error',
          detail: 'Unable to connect to the server. Please check your internet connection and ensure the backend is running.',
          code: 'NETWORK_ERROR',
        }
      }
      
      return {
        error: 'Network error',
        detail: 'Unable to connect to the server. Please check your connection.',
        code: 'NETWORK_ERROR',
      }
    }

    return {
      error: 'Unknown error',
      detail: error.message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
    }
  }

  async transcribeAudio(
    file: File,
    language?: string,
    onUploadProgress?: (progress: number) => void
  ): Promise<TranscriptionResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (language) {
      formData.append('language', language)
    }

    let lastReportedProgress = 0

    // Report initial progress to show upload has started
    if (onUploadProgress) {
      onUploadProgress(1) // Show 1% to indicate upload started
      lastReportedProgress = 1
    }

    const response = await this.client.post<TranscriptionResponse>(
      '/transcribe',
      formData,
      {
        onUploadProgress: (progressEvent) => {
          if (!onUploadProgress) return
          
          let progress = 0
          
          if (progressEvent.total && progressEvent.total > 0) {
            // Use actual progress from server
            progress = Math.min(
              Math.round((progressEvent.loaded * 100) / progressEvent.total),
              99 // Cap at 99% until response is received
            )
          } else if (progressEvent.loaded && file.size > 0) {
            // Estimate based on file size when total is not available
            progress = Math.min(
              Math.round((progressEvent.loaded / file.size) * 100),
              99
            )
          } else if (progressEvent.loaded > 0) {
            // If we have some data loaded but no size info, show minimal progress
            progress = Math.min(lastReportedProgress + 1, 10)
          }
          
          // Only report progress if it increased (prevent resets)
          if (progress > lastReportedProgress) {
            lastReportedProgress = progress
            onUploadProgress(progress)
          }
        },
      }
    )

    // Ensure 100% is reported if not already done
    if (onUploadProgress && lastReportedProgress < 100) {
      onUploadProgress(100)
    }

    return response.data
  }

  async checkHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health')
    return response.data
  }
}

export const apiClient = new ApiClient()
