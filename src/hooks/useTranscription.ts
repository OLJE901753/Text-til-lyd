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
        const result = await apiClient.transcribeAudio(
          file,
          language,
          onProgress
        )

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
