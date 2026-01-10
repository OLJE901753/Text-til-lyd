import { useState, useCallback } from 'react'
import { TranscriptionResponse, TranscriptionStatus } from '@/types'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export interface TranscriptionState {
  status: TranscriptionStatus
  result: TranscriptionResponse | null
  error: string | null
}

export function useTranscription() {
  const { toast } = useToast()
  const [state, setState] = useState<TranscriptionState>({
    status: 'idle',
    result: null,
    error: null,
  })

  const transcribe = useCallback(
    async (file: File, language?: string, onProgress?: (progress: number) => void) => {
      setState({
        status: 'uploading',
        result: null,
        error: null,
      })

      // Timeout watchdog: if stuck in processing for > 3 minutes, show error
      const processingTimeout = 3 * 60 * 1000 // 3 minutes
      const uploadTimeout = 2 * 60 * 1000 // 2 minutes for upload
      let timeoutId: NodeJS.Timeout | null = null
      let uploadTimeoutId: NodeJS.Timeout | null = null
      let isCancelled = false

      const clearProcessingTimeout = () => {
        if (timeoutId) {
          clearTimeout(timeoutId)
          timeoutId = null
        }
      }
      
      const clearUploadTimeout = () => {
        if (uploadTimeoutId) {
          clearTimeout(uploadTimeoutId)
          uploadTimeoutId = null
        }
      }

      const setProcessingTimeout = () => {
        clearTimeout()
        timeoutId = setTimeout(() => {
          if (!isCancelled) {
            const timeoutMessage = 'Transcription is taking longer than expected. The file may be very large or the server may be overloaded. Please try again or use a smaller file.'
            setState({
              status: 'error',
              result: null,
              error: timeoutMessage,
            })
            toast({
              title: 'Timeout Error',
              description: timeoutMessage,
              variant: 'destructive',
            })
          }
        }, processingTimeout)
      }

      try {
        // Track upload progress and transition to processing when upload completes
        let uploadCompleted = false
        let lastProgress = 0
        let lastProgressTime = Date.now()
        let uploadStartTime = Date.now()

        // Set upload timeout
        uploadTimeoutId = setTimeout(() => {
          if (!uploadCompleted && !isCancelled) {
            const uploadTimeoutMessage = 'Upload is taking too long. Please check your connection and try again.'
            setState({
              status: 'error',
              result: null,
              error: uploadTimeoutMessage,
            })
            toast({
              title: 'Upload Timeout',
              description: uploadTimeoutMessage,
              variant: 'destructive',
            })
            isCancelled = true
          }
        }, uploadTimeout)

        const result = await apiClient.transcribeAudio(
          file,
          language,
          (progress) => {
            lastProgressTime = Date.now()
            // Only process progress updates that are increasing (prevent resets)
            if (progress >= lastProgress) {
              lastProgress = progress
              
              // Call the provided progress callback
              if (onProgress) {
                onProgress(progress)
              }
              
              // Transition to processing when upload reaches 100%
              if (progress >= 100 && !uploadCompleted) {
                clearUploadTimeout()
                uploadCompleted = true
                setState((prev) => {
                  // Only update if still in uploading state
                  if (prev.status === 'uploading') {
                    return {
                      ...prev,
                      status: 'processing',
                    }
                  }
                  return prev
                })
                // Set processing timeout watchdog
                setProcessingTimeout()
              }
            }
          }
        )

        clearUploadTimeout()

        // Ensure we transition to processing if not already there
        setState((prev) => {
          if (prev.status === 'uploading') {
            return {
              ...prev,
              status: 'processing',
            }
          }
          return prev
        })

        // Set processing timeout if not already set
        if (!timeoutId) {
          setProcessingTimeout()
        }

        // Small delay to ensure processing state is visible
        await new Promise(resolve => setTimeout(resolve, 300))

        clearProcessingTimeout() // Clear timeout on success

        setState({
          status: 'completed',
          result,
          error: null,
        })

        toast({
          title: 'Success!',
          description: 'Audio transcribed successfully',
        })

        return result
      } catch (error: any) {
        clearProcessingTimeout()
        clearUploadTimeout()
        isCancelled = true

        // Detect specific error types and provide actionable messages
        let errorMessage = error.detail || error.message || 'Transcription failed'
        let errorTitle = 'Error'
        
        // Network/timeout errors
        if (error.code === 'ECONNABORTED' || error.code === 'TIMEOUT' || error.message?.includes('timeout')) {
          errorTitle = 'Timeout Error'
          errorMessage = 'The request timed out. This may happen if the file is very large or the server is overloaded. Please try again or use a smaller file.'
        } else if (error.code === 'NETWORK_ERROR' || !error.response) {
          errorTitle = 'Connection Error'
          errorMessage = 'Unable to connect to the server. Please check your internet connection and ensure the backend is running.'
        } else if (error.response?.status === 504) {
          errorTitle = 'Timeout Error'
          errorMessage = 'The transcription operation timed out. The file may be too large or the processing is taking too long. Please try a smaller file.'
        } else if (error.response?.status === 500) {
          errorTitle = 'Server Error'
          errorMessage = error.detail || 'An error occurred on the server. Please try again. If the problem persists, the file may be corrupted or in an unsupported format.'
        } else if (error.response?.status === 413) {
          errorTitle = 'File Too Large'
          errorMessage = 'The file exceeds the maximum allowed size. Please use a smaller file (maximum 100MB).'
        } else if (error.response?.status === 400) {
          errorTitle = 'Invalid File'
          errorMessage = error.detail || 'The file format is not supported or the file is invalid. Please use a valid audio file (MP3, WAV, M4A, WebM, or OGG).'
        }
        
        setState({
          status: 'error',
          result: null,
          error: errorMessage,
        })

        toast({
          title: errorTitle,
          description: errorMessage,
          variant: 'destructive',
        })

        throw error
      }
    },
    [toast]
  )

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      result: null,
      error: null,
    })
  }, [])

  return {
    ...state,
    transcribe,
    reset,
  }
}
