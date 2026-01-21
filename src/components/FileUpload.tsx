import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, FileAudio } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatFileSize } from '@/lib/utils'
import { MAX_FILE_SIZE_BYTES, ALLOWED_AUDIO_TYPES } from '@/lib/constants'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  onCancel?: () => void
  uploadProgress?: number
  isUploading?: boolean
  className?: string
}

export function FileUpload({
  onFileSelect,
  onCancel,
  uploadProgress = 0,
  isUploading = false,
  className,
}: FileUploadProps) {
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(MAX_FILE_SIZE_BYTES)})`
    }

    // Check file extension
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!extension || !ALLOWED_AUDIO_TYPES.includes(extension as any)) {
      return `File type not supported. Allowed types: ${ALLOWED_AUDIO_TYPES.join(', ')}`
    }

    return null
  }

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError(null)

      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0]
        if (rejection.errors) {
          const error = rejection.errors[0]
          setError(error.message || 'File rejected')
        }
        return
      }

      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        const validationError = validateFile(file)
        
        if (validationError) {
          setError(validationError)
          return
        }

        setSelectedFile(file)
        onFileSelect(file)
      }
    },
    [onFileSelect]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ALLOWED_AUDIO_TYPES.map(ext => `.${ext}`),
    },
    maxSize: MAX_FILE_SIZE_BYTES,
    multiple: false,
  })

  const handleRemove = () => {
    setSelectedFile(null)
    setError(null)
    onCancel?.()
  }

  return (
    <div className={cn('space-y-4', className)}>
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={cn(
            'glass-card border-2 border-dashed p-8 text-center cursor-pointer transition-all',
            isDragActive
              ? 'border-primary bg-primary/10 scale-105'
              : 'border-lime-500/30 hover:border-lime-500/50 hover:scale-[1.02]',
            className
          )}
          role="button"
          tabIndex={0}
          aria-label="Upload audio file"
        >
          <input {...getInputProps()} />
          <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground animate-float" />
          <p className="text-lg font-medium mb-2">
            {isDragActive ? 'Drop the file here' : 'Drag & drop audio file'}
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Supported: {ALLOWED_AUDIO_TYPES.join(', ').toUpperCase()} (max {formatFileSize(MAX_FILE_SIZE_BYTES)})
          </p>
        </div>
      ) : (
        <div className="glass-card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileAudio className="h-8 w-8 text-primary" />
              <div>
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            <Button
              onClick={handleRemove}
              size="icon"
              variant="ghost"
              disabled={isUploading}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{Math.round(uploadProgress)}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
