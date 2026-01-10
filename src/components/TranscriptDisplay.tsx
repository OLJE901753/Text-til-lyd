import { useState } from 'react'
import { Copy, Check, Download as DownloadIcon, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TranscriptionResponse } from '@/types'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

interface TranscriptDisplayProps {
  transcript: TranscriptionResponse | null
  className?: string
}

export function TranscriptDisplay({ transcript, className }: TranscriptDisplayProps) {
  const { toast } = useToast()
  const [copied, setCopied] = useState(false)

  if (!transcript) {
    return null
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(transcript.transcript)
      setCopied(true)
      toast({
        title: 'Copied!',
        description: 'Transcript copied to clipboard',
      })
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to copy transcript',
        variant: 'destructive',
      })
    }
  }

  const handleDownload = (format: 'txt' | 'srt' | 'vtt') => {
    let content = ''
    const filename = `transcript.${format}`

    switch (format) {
      case 'txt':
        content = transcript.transcript
        break
      case 'srt':
        content = generateSRT(transcript)
        break
      case 'vtt':
        content = generateVTT(transcript)
        break
    }

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast({
      title: 'Downloaded!',
      description: `Transcript saved as ${filename}`,
    })
  }

  const generateSRT = (data: TranscriptionResponse): string => {
    if (!data.segments || data.segments.length === 0) {
      return data.transcript
    }

    return data.segments
      .map((seg, index) => {
        const start = formatSRTTime(seg.start)
        const end = formatSRTTime(seg.end)
        return `${index + 1}\n${start} --> ${end}\n${seg.text}\n`
      })
      .join('\n')
  }

  const generateVTT = (data: TranscriptionResponse): string => {
    let vtt = 'WEBVTT\n\n'
    
    if (!data.segments || data.segments.length === 0) {
      return vtt + data.transcript
    }

    vtt += data.segments
      .map((seg) => {
        const start = formatVTTTime(seg.start)
        const end = formatVTTTime(seg.end)
        return `${start} --> ${end}\n${seg.text}\n`
      })
      .join('\n')

    return vtt
  }

  const formatSRTTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const ms = Math.floor((seconds % 1) * 1000)
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`
  }

  const formatVTTTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const ms = Math.floor((seconds % 1) * 1000)
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`
  }

  return (
    <Card className={cn('glass-card', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Transcript</CardTitle>
          <div className="flex gap-2">
            <Button
              onClick={handleCopy}
              size="sm"
              variant="outline"
              className="gap-2"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy
                </>
              )}
            </Button>
            <Button
              onClick={() => handleDownload('txt')}
              size="sm"
              variant="outline"
              className="gap-2"
            >
              <DownloadIcon className="h-4 w-4" />
              TXT
            </Button>
            <Button
              onClick={() => handleDownload('srt')}
              size="sm"
              variant="outline"
              className="gap-2"
            >
              <DownloadIcon className="h-4 w-4" />
              SRT
            </Button>
            <Button
              onClick={() => handleDownload('vtt')}
              size="sm"
              variant="outline"
              className="gap-2"
            >
              <DownloadIcon className="h-4 w-4" />
              VTT
            </Button>
          </div>
        </div>
        {transcript.language && (
          <p className="text-sm text-muted-foreground">
            Language: {transcript.language.toUpperCase()}
            {transcript.confidence && (
              <span className="ml-2">
                (Confidence: {Math.round(transcript.confidence * 100)}%)
              </span>
            )}
          </p>
        )}
      </CardHeader>
      <CardContent>
        {transcript.confidence_warning && (
          <Alert variant="default" className="mb-4 border-yellow-500/50 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400">
            <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
            <AlertDescription>
              Low confidence transcription detected ({(transcript.confidence ? Math.round(transcript.confidence * 100) : 'N/A')}%).
              The audio quality may be poor or the language may be unclear. Please review the transcript carefully.
            </AlertDescription>
          </Alert>
        )}
        <div className="prose prose-invert max-w-none animate-fade-in">
          <p className="whitespace-pre-wrap text-foreground leading-relaxed">
            {transcript.transcript}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
