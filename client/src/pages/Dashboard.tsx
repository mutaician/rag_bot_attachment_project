import { useEffect } from 'react'
import { getDocuments } from '../api/client'

/**
 * Document dashboard — lists uploaded files and indexing status.
 * Milestone 1 checkpoint: fetch mock docs from the API and log to console.
 */
export default function Dashboard() {
  useEffect(() => {
    // Runs once when this page mounts — good place for initial data loading
    getDocuments()
      .then((data) => console.log('Mock documents:', data))
      .catch((err) => console.error('Failed to fetch documents:', err))
  }, []) // empty deps = run only on mount

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-100">Documents</h1>
      <p className="mt-2 text-gray-400">
        Open devtools console (F12) to see the mock API response.
      </p>
    </div>
  )
}
