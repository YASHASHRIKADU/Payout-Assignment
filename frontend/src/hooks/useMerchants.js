import { useState, useEffect, useCallback } from 'react'
import { getMerchants } from '../api/client'

export function useMerchants() {
  const [merchants, setMerchants] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchMerchants = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getMerchants()
      setMerchants(res.data)
      setError(null)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load merchants')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMerchants()
  }, [fetchMerchants])

  return { merchants, loading, error }
}
