import { useState, useEffect } from 'react'
import { FileUpload } from '@/components/FileUpload'
import { AudioPlayer } from '@/components/AudioPlayer'
import { TranscriptDisplay } from '@/components/TranscriptDisplay'
import { LoadingState } from '@/components/LoadingState'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useTranscription } from '@/hooks/useTranscription'
import { apiClient } from '@/lib/api'
import { Mic } from 'lucide-react'

export default function Transcription() {
  const fileUpload = useFileUpload()
  const transcription = useTranscription()
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  useEffect(() => {
    if (fileUpload.file) {
      const url = URL.createObjectURL(fileUpload.file)
      setAudioUrl(url)
      return () => URL.revokeObjectURL(url)
    } else {
      setAudioUrl(null)
    }
  }, [fileUpload.file])

  const handleFileSelect = async (file: File) => {
    // Reset any previous state
    fileUpload.selectFile(file)
    fileUpload.setUploading(true)
    fileUpload.setError(null)
    fileUpload.setUploadProgress(0)
    
    try {
      // Check backend health before starting
      try {
        await apiClient.checkHealth()
      } catch (healthError) {
        throw new Error('Backend service is not available. Please ensure the server is running.')
      }
      
      // Track the highest progress to prevent resets
      let maxProgress = 0
      
      // Start transcription - it will handle upload and processing states
      await transcription.transcribe(
        file,
        undefined, // Auto-detect language
        (progress) => {
          // Only update if progress increased (prevent resets)
          if (progress >= maxProgress) {
            maxProgress = progress
            fileUpload.setUploadProgress(progress)
          } else {
            // Log if progress decreases (shouldn't happen)
            console.warn(`Progress decreased from ${maxProgress}% to ${progress}% - ignoring`)
          }
        }
      )
      
      // Transcription completed successfully
      fileUpload.setUploading(false)
      fileUpload.setUploadProgress(100)
    } catch (error: any) {
      // Error handling with detailed logging
      console.error('Transcription error:', error)
      const errorMessage = error.detail || error.message || 'Transcription failed'
      fileUpload.setError(errorMessage)
      fileUpload.setUploading(false)
      // Keep progress at current value on error so user can see what happened
    }
  }

  const handleCancel = () => {
    fileUpload.reset()
    transcription.reset()
    setAudioUrl(null)
  }

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <Card className="glass-card border-lime-500/30">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
              <Mic className="h-8 w-8 text-primary" />
              <CardTitle className="text-3xl gradient-text font-bold">
                Audio Transcription
              </CardTitle>
            </div>
            <CardDescription className="text-gray-300">
              Upload an audio file to transcribe with 90-95% accuracy
            </CardDescription>
          </CardHeader>
        </Card>

        {/* File Upload */}
        <FileUpload
          onFileSelect={handleFileSelect}
          onCancel={handleCancel}
          uploadProgress={fileUpload.uploadProgress}
          isUploading={
            fileUpload.isUploading || 
            transcription.status === 'uploading' || 
            transcription.status === 'processing'
          }
        />

        {/* Audio Player */}
        {audioUrl && fileUpload.file && (
          <AudioPlayer src={audioUrl} />
        )}

        {/* Loading State */}
        {(transcription.status === 'processing' || 
          transcription.status === 'uploading' ||
          (fileUpload.isUploading && fileUpload.uploadProgress < 100)) && (
          <LoadingState
            message={
              transcription.status === 'processing'
                ? "Transcribing audio... This may take a moment."
                : transcription.status === 'uploading'
                ? "Uploading file..."
                : "Processing..."
            }
            variant="inline"
          />
        )}

        {/* Transcript Display */}
        {transcription.status === 'completed' && transcription.result && (
          <div className="animate-slide-up">
            <TranscriptDisplay transcript={transcription.result} />
          </div>
        )}

        {/* Error Display */}
        {transcription.status === 'error' && transcription.error && (
          <Card className="glass-card border-destructive/50">
            <CardHeader>
              <CardTitle className="text-destructive">Error</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {transcription.error}
              </p>
              <button
                onClick={handleCancel}
                className="text-sm text-primary hover:underline"
                aria-label="Try again"
              >
                Try again
              </button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
