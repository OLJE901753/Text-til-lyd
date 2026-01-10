/**
 * Health check utility for frontend
 * Monitors backend connectivity and system health
 */

import { apiClient } from '@/lib/api'

export interface HealthStatus {
  backend: 'healthy' | 'unhealthy' | 'checking'
  lastCheck: Date | null
  error?: string
}

let healthStatus: HealthStatus = {
  backend: 'checking',
  lastCheck: null,
}

/**
 * Check backend health
 */
export async function checkBackendHealth(): Promise<HealthStatus> {
  try {
    const response = await apiClient.checkHealth()
    healthStatus = {
      backend: response.status === 'healthy' ? 'healthy' : 'unhealthy',
      lastCheck: new Date(),
    }
    return healthStatus
  } catch (error: any) {
    healthStatus = {
      backend: 'unhealthy',
      lastCheck: new Date(),
      error: error.message || 'Backend health check failed',
    }
    return healthStatus
  }
}

/**
 * Get current health status
 */
export function getHealthStatus(): HealthStatus {
  return { ...healthStatus }
}

/**
 * Setup periodic health checks
 */
export function setupHealthChecks(intervalMs: number = 30000): () => void {
  // Initial check
  checkBackendHealth()
  
  // Periodic checks
  const intervalId = setInterval(() => {
    checkBackendHealth()
  }, intervalMs)
  
  // Return cleanup function
  return () => clearInterval(intervalId)
}
