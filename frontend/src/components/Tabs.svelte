<script>
  let { tabs, active, onchange } = $props();
</script>

<div class="tabs">
  {#each tabs as t}
    <button class="tab" class:active={active === t.id} onclick={() => onchange(t.id)}>
      {t.label}
    </button>
  {/each}
</div>

<style>
  .tabs {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .tab {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 18px;
    border-radius: 999px;
    transition: all 0.15s;
  }
  .tab:hover {
    color: var(--text);
    border-color: var(--border-strong);
  }
  .tab.active {
    color: var(--on-accent);
    border-color: transparent;
    background: var(--yellow);
  }
</style>
