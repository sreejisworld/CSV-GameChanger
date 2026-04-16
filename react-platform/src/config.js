// Central API config — all fetch calls must use this, never hardcode localhost
export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
