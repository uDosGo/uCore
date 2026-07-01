/**
 * @module composables/useApi
 * @description Composable for making reactive API calls with loading/error state.
 * @returns {data, loading, error, execute}
 * @usage
 *   const { data, loading, error, execute } = useApi(() => api.snackbar.status())
 *   onMounted(execute)
 */
import { ref, type Ref } from 'vue'

interface UseApiReturn<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  execute: () => Promise<void>
}

export function useApi<T>(fn: () => Promise<{ data: T; ok: boolean }>): UseApiReturn<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute() {
    loading.value = true
    error.value = null
    try {
      const result = await fn()
      if (result.ok) {
        data.value = result.data
      } else {
        error.value = 'Request failed'
      }
    } catch (e: any) {
      error.value = e.message || 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
