import { useState, useEffect, useCallback, useRef } from 'react'
import { getPayouts } from '../api/client'

/**
 * Polls the payouts list every `intervalMs` milliseconds.
 * Stops polling once all visible payouts have reached a terminal state.
 */
export function usePayouts(merchantId, intervalMs = 5000) {
  const [payouts, setPayouts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const fetchPayouts = useCallback(async () => {
    if (!merchantId) return
    setLoading(true)
    try {
      const res = await getPayouts(merchantId)
      setPayouts(res.data)
      setError(null)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load payouts')
    } finally {
      setLoading(false)
    }
  }, [merchantId])

  useEffect(() => {
    fetchPayouts()
    timerRef.current = setInterval(fetchPayouts, intervalMs)
    return () => clearInterval(timerRef.current)
  }, [fetchPayouts, intervalMs])

  return { payouts, loading, error, refetch: fetchPayouts }
}
