/**
 * @module types
 * @description Central type exports for the Vue frontend.
 */
export * from './filepicker'

export interface SurfaceCard {
  id: string
  title: string
  description: string
  icon: string
  route: string
  color: string
  starred?: boolean
  status?: 'running' | 'stopped' | 'error'
}

export interface SnackItem {
  id: string
  title: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
}
