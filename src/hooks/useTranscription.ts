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

      try {
        // Track upload progress and transition to processing when upload completes
        let uploadCompleted = false
        let lastProgress = 0
        
        const result = await apiClient.transcribeAudio(
          file,
          language,
          (progress) => {
            // Only process progress updates that are increasing (prevent resets)
            if (progress >= lastProgress) {
              lastProgress = progress
              
              // Call the provided progress callback
              if (onProgress) {
                onProgress(progress)
              }
              
              // Transition to processing when upload reaches 100%
              if (progress >= 100 && !uploadCompleted) {
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
              }
            }
          }
        )

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

        // Small delay to ensure processing state is visible
        await new Promise(resolve => setTimeout(resolve, 300))

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
        const errorMessage =
          error.detail || error.message || 'Transcription failed'
        
        setState({
          status: 'error',
          result: null,
          error: errorMessage,
        })

        toast({
          title: 'Error',
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
