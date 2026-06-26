// Backend base URL. Override at build/run time with VITE_API_BASE.
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export async function fetchTournament() {
  const res = await fetch(`${API_BASE}/api/tournament`);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}
