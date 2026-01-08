export interface TranscriptionResponse {
  transcript: string
  language?: string
  confidence?: number
  duration?: number
  segments?: TranscriptionSegment[]
  model: string
}

export interface TranscriptionSegment {
  id: number
  seek: number
  start: number
  end: number
  text: string
  tokens: number[]
  temperature: number
  avg_logprob: number
  compression_ratio: number
  no_speech_prob: number
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  model_loaded?: boolean
  model_name?: string
}

export interface ErrorResponse {
  error: string
  detail?: string
  code?: string
}

export type TranscriptionStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
