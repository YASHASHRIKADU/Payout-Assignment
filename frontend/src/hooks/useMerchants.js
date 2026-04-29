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
      // If the API returns an object (like a paginated response) or HTML, handle it safely
      const data = res.data?.results || res.data
      if (Array.isArray(data)) {
        setMerchants(data)
        setError(null)
      } else {
        setMerchants([])
        setError('Backend did not return an array. Check VITE_API_BASE_URL.')
      }
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
