import { useState, useCallback } from 'react'

export interface FileUploadState {
  file: File | null
  isUploading: boolean
  uploadProgress: number
  error: string | null
}

export function useFileUpload() {
  const [state, setState] = useState<FileUploadState>({
    file: null,
    isUploading: false,
    uploadProgress: 0,
    error: null,
  })

  const selectFile = useCallback((file: File) => {
    setState({
      file,
      isUploading: false,
      uploadProgress: 0,
      error: null,
    })
  }, [])

  const setUploadProgress = useCallback((progress: number) => {
    setState((prev) => ({
      ...prev,
      uploadProgress: progress,
    }))
  }, [])

  const setUploading = useCallback((isUploading: boolean) => {
    setState((prev) => ({
      ...prev,
      isUploading,
      uploadProgress: isUploading ? 0 : prev.uploadProgress,
    }))
  }, [])

  const setError = useCallback((error: string | null) => {
    setState((prev) => ({
      ...prev,
      error,
    }))
  }, [])

  const reset = useCallback(() => {
    setState({
      file: null,
      isUploading: false,
      uploadProgress: 0,
      error: null,
    })
  }, [])

  return {
    ...state,
    selectFile,
    setUploadProgress,
    setUploading,
    setError,
    reset,
  }
}
