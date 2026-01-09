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
      timeout: 300000, // 5 minutes for large files
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
      // Network error - retry
      return true
    }

    const status = error.response.status
    // Retry on 5xx errors and 429 (rate limit)
    return status >= 500 || status === 429
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
      return {
        error: 'Network error',
        detail: 'Unable to connect to the server. Please check your connection.',
        code: 'NETWORK_ERROR',
      }
    }

    return {
      error: 'Unknown error',
      detail: error.message,
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

    const response = await this.client.post<TranscriptionResponse>(
      '/transcribe',
      formData,
      {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onUploadProgress) {
            const progress = Math.min(
              Math.round((progressEvent.loaded * 100) / progressEvent.total),
              100
            )
            
            // Only report progress if it increased (prevent resets)
            if (progress >= lastReportedProgress) {
              lastReportedProgress = progress
              onUploadProgress(progress)
            } else if (progress === 100 && lastReportedProgress < 100) {
              // Ensure we always report 100% when upload completes
              lastReportedProgress = 100
              onUploadProgress(100)
            }
          } else if (progressEvent.loaded && progressEvent.total === undefined && onUploadProgress) {
            // Handle case where total is not available yet
            // Estimate based on file size
            const estimatedProgress = Math.min(
              Math.round((progressEvent.loaded / file.size) * 100),
              99
            )
            if (estimatedProgress > lastReportedProgress) {
              lastReportedProgress = estimatedProgress
              onUploadProgress(estimatedProgress)
            }
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
