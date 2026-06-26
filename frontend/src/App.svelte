<script>
  import { onMount } from 'svelte';
  import { tournament, activeTab, status, startPolling } from './stores.js';
  import Tabs from './components/Tabs.svelte';
  import BracketView from './components/BracketView.svelte';
  import GroupsView from './components/GroupsView.svelte';
  import StatisticsView from './components/StatisticsView.svelte';

  const TABS = [
    { id: 'bracket', label: 'Bracket' },
    { id: 'groups', label: 'Groups' },
    { id: 'statistics', label: 'Statistics' },
  ];

  onMount(() => startPolling());

  function fmtUpdated(iso) {
    if (!iso) return '';
    return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  }

  // Future interactivity hook — currently just logs the selected match.
  function onselect(match) {
    console.log('selected match', match);
  }
</script>

<header class="topbar">
  <div class="brand">
    <span class="mark"></span>
    <div class="title">
      <h1>{$tournament?.competition?.name ?? 'Knockout stage'}</h1>
    </div>
  </div>
  <div class="meta">
    {#if $status.error}
      <span class="err">offline — {$status.error}</span>
    {:else if $status.updatedAt}
      <span class="upd"><span class="dot"></span>Updated {fmtUpdated($status.updatedAt)}</span>
    {/if}
  </div>
</header>

<div class="tabbar">
  <Tabs
    tabs={TABS}
    active={$activeTab}
    onchange={(id) => {
      activeTab.set(id);
      location.hash = id;
    }}
  />
</div>

<main>
  {#if $status.loading && !$tournament}
    <div class="placeholder">Loading tournament…</div>
  {:else if !$tournament}
    <div class="placeholder">No data. Is the backend running on :8000?</div>
  {:else if $activeTab === 'bracket'}
    <BracketView bracket={$tournament.bracket} {onselect} />
  {:else if $activeTab === 'groups'}
    <GroupsView groups={$tournament.groups} />
  {:else if $activeTab === 'statistics'}
    <StatisticsView statistics={$tournament.statistics} />
  {/if}
</main>

<style>
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 28px 14px;
    gap: 16px;
    flex-wrap: wrap;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .title h1 {
    margin: 0;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: -0.3px;
  }
  .meta .upd {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    color: var(--muted);
  }
  .meta .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
  }
  .meta .err {
    font-size: 12px;
    color: var(--live);
  }
  .tabbar {
    padding: 4px 28px 16px;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--scrim);
    backdrop-filter: blur(10px);
    z-index: 10;
  }
  main {
    padding: 22px 28px 60px;
    max-width: 1700px;
    margin: 0 auto;
  }
  .placeholder {
    padding: 80px 0;
    text-align: center;
    color: var(--muted);
  }
</style>
