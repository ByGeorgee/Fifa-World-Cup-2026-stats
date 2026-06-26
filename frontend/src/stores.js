import { writable } from 'svelte/store';
import { fetchTournament } from './lib/api.js';

const VALID_TABS = ['bracket', 'groups', 'statistics'];
const initialTab =
  typeof location !== 'undefined' && VALID_TABS.includes(location.hash.slice(1))
    ? location.hash.slice(1)
    : 'bracket';

export const tournament = writable(null);
export const activeTab = writable(initialTab); // 'bracket' | 'groups' | 'statistics'
export const status = writable({ loading: true, error: null, updatedAt: null });

// Poll the backend every 3 minutes (matches the backend poll cadence).
const REFRESH_MS = 3 * 60 * 1000;

async function load() {
  try {
    const data = await fetchTournament();
    tournament.set(data);
    status.set({ loading: false, error: null, updatedAt: data.generated_at });
  } catch (err) {
    status.update((s) => ({ ...s, loading: false, error: String(err) }));
  }
}

export function startPolling() {
  load();
  const id = setInterval(load, REFRESH_MS);
  return () => clearInterval(id);
}
