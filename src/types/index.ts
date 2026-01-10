export interface TranscriptionResponse {
  transcript: string
  language?: string
  confidence?: number
  confidence_warning?: boolean
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
  device?: string
  gpu_info?: {
    name?: string
    vram_total_gb?: number
    vram_free_gb?: number
    cuda_version?: string
    device_count?: number
  }
  cuda_available?: boolean
  cuda_device_count?: number
}

export interface ErrorResponse {
  error: string
  detail?: string
  code?: string
}

export type TranscriptionStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
