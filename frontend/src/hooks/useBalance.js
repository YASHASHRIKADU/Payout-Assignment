import { useState, useEffect, useCallback } from 'react'
import { getBalance } from '../api/client'

export function useBalance(merchantId) {
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchBalance = useCallback(async () => {
    if (!merchantId) return
    setLoading(true)
    try {
      const res = await getBalance(merchantId)
      setBalance(res.data)
      setError(null)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load balance')
    } finally {
      setLoading(false)
    }
  }, [merchantId])

  useEffect(() => {
    fetchBalance()
  }, [fetchBalance])

  return { balance, loading, error, refetch: fetchBalance }
}
