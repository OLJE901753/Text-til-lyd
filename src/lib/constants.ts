export const MAX_FILE_SIZE_MB = 100
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

export const ALLOWED_AUDIO_TYPES = ['m4a', 'mp3', 'wav', 'webm', 'ogg'] as const
export const ALLOWED_MIME_TYPES = [
  'audio/mpeg',
  'audio/mp4',
  'audio/wav',
  'audio/wave',
  'audio/x-wav',
  'audio/webm',
  'audio/ogg',
  'audio/vorbis',
  'audio/x-m4a',
] as const

export const API_BASE_URL = '/api'
