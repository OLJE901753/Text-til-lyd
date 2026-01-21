import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Toaster } from '@/components/ui/toaster'
import { LoadingState } from '@/components/LoadingState'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { setupHealthChecks } from '@/utils/healthCheck'

// Lazy load pages for code splitting
const Transcription = lazy(() => import('@/pages/Transcription'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

function App() {
  // Setup health checks on mount
  useEffect(() => {
    const cleanup = setupHealthChecks(30000) // Check every 30 seconds
    return cleanup
  }, [])

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Suspense fallback={<LoadingState message="Loading..." variant="overlay" />}>
            <Routes>
              <Route path="/" element={<Transcription />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
        <Toaster />
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
