<script>
  import { tick } from 'svelte';
  import MatchCard from './MatchCard.svelte';
  import { localTimeZoneLabel } from '../lib/time.js';
  import { computeBracketLayout } from '../lib/bracketLayout.js';

  let { bracket, onselect = null } = $props();

  // Group-stage matches (12 groups × 6), shown as a leftmost column before the knockout pyramid.
  // Absent unless the backend has it enabled (FIFA_SHOW_GROUP_STAGE).
  const groupStage = $derived(bracket?.group_stage ?? []);
  let showAll = $state(true); // true = all 72 matches, false = only played/live

  // Order each round so feeding matches are adjacent (post-order DFS from the final), which makes
  // the column-of-matches lay out as a proper left-to-right pyramid. See lib/bracketLayout.js.
  const layout = $derived(computeBracketLayout(bracket));

  // ---- measured SVG connectors -------------------------------------------------
  let scrollEl = $state(null);
  const cardEls = new Map();
  let connectors = $state([]);
  let svgW = $state(0);
  let svgH = $state(0);

  function register(node, id) {
    cardEls.set(id, node);
    return { destroy: () => cardEls.delete(id) };
  }

  function recompute() {
    if (!scrollEl || !bracket) return;
    const base = scrollEl.getBoundingClientRect();
    const ox = scrollEl.scrollLeft - base.left;
    const oy = scrollEl.scrollTop - base.top;
    svgW = scrollEl.scrollWidth;
    svgH = scrollEl.scrollHeight;

    // Draw from the layout's merged link set — this includes the winner links that
    // reconstruction recovered for played matches, whose feeds_into ESPN has erased.
    const lines = [];
    for (const { child, parent } of layout.links) {
      const childEl = cardEls.get(child);
      const parentEl = cardEls.get(parent);
      if (!childEl || !parentEl) continue;
      const c = childEl.getBoundingClientRect();
      const p = parentEl.getBoundingClientRect();
      const x1 = c.right + ox, y1 = c.top + c.height / 2 + oy;
      const x2 = p.left + ox, y2 = p.top + p.height / 2 + oy;
      const midX = x1 + Math.max(12, (x2 - x1) / 2);
      // Orthogonal connector. Round only the outer elbow (where each child's
      // line turns down/up); keep the inner corner sharp — that's where the two
      // sibling lines converge into the parent. Clamp radius to the shortest leg.
      const dirY = y2 >= y1 ? 1 : -1;
      const r = Math.min(12, midX - x1, Math.abs(y2 - y1));
      lines.push({
        d:
          `M ${x1} ${y1} ` +
          `L ${midX - r} ${y1} ` +
          `Q ${midX} ${y1} ${midX} ${y1 + dirY * r} ` +
          `L ${midX} ${y2} ` +
          `L ${x2} ${y2}`,
      });
    }
    connectors = lines;
  }

  // Recompute after the DOM settles whenever the bracket data changes, and on resize/scroll.
  $effect(() => {
    bracket; // track
    let raf2;
    const raf1 = requestAnimationFrame(() => {
      recompute();
      raf2 = requestAnimationFrame(recompute); // second pass once flags/images reflow
    });
    return () => {
      cancelAnimationFrame(raf1);
      if (raf2) cancelAnimationFrame(raf2);
    };
  });

  $effect(() => {
    if (!scrollEl) return;
    const onScroll = () => recompute();
    const ro = new ResizeObserver(() => recompute());
    ro.observe(scrollEl);
    scrollEl.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      ro.disconnect();
      scrollEl.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  });
</script>

<div class="bracket-wrap">
  <div class="tz-note">Times shown in your local timezone ({localTimeZoneLabel()})</div>

  <div class="scroll" bind:this={scrollEl}>
    <svg class="links" width={svgW} height={svgH} aria-hidden="true">
      {#each connectors as c}
        <path d={c.d} />
      {/each}
    </svg>

    <div class="columns">
      {#if groupStage.length}
        <div class="col group-col">
          <div class="col-head">Group stage</div>
          <div class="gs-toggle">
            <button class:active={showAll} onclick={() => (showAll = true)}>All</button>
            <button class:active={!showAll} onclick={() => (showAll = false)}>Played</button>
          </div>
          <div class="col-body gs-body">
            {#each groupStage as g (g.group)}
              {@const matches = showAll ? g.matches : g.matches.filter((m) => m.status !== 'scheduled')}
              {#if matches.length}
                <div class="gs-group">
                  <div class="gs-head">{g.label}</div>
                  {#each matches as m (m.id)}
                    <div class="cell"><MatchCard match={m} compact {onselect} /></div>
                  {/each}
                </div>
              {/if}
            {/each}
          </div>
        </div>
      {/if}

      {#each layout.columns as col (col.key)}
        <div class="col">
          <div class="col-head">{col.label}</div>
          <div class="col-body">
            {#each col.matches as m (m.id)}
              <div class="cell" class:final-match={m.id === 'final'} use:register={m.id}>
                <MatchCard match={m} {onselect} />
              </div>
            {/each}

            {#if col.key === 'final' && layout.third}
              <div class="third" style="position: absolute; width: 232px; top: calc(50% + 200px);">
                <div class="third-head">Third-place play-off</div>
                <div class="cell" use:register={layout.third.id}>
                  <MatchCard match={layout.third} compact {onselect} />
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .bracket-wrap {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .tz-note {
    font-size: 12px;
    color: var(--muted-2);
    padding: 0 4px;
  }
  .scroll {
    position: relative;
    overflow: auto;
    padding: 8px 4px 24px;
  }
  .links {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
    z-index: 0;
  }
  .links path {
    fill: none;
    stroke: var(--connector);
    stroke-width: 1.5;
  }

  .columns {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 56px;
    min-width: min-content;
    align-items: stretch;
  }
  .col {
    display: flex;
    flex-direction: column;
    flex: 0 0 232px;
    width: 232px;
  }
  .col-head {
    text-align: center;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    padding-bottom: 12px;
    margin-bottom: 4px;
  }
  .col-body {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    gap: 10px;
  }
  .cell {
    width: 100%;
  }
  .final-match {
    outline: 2px solid var(--yellow);
    outline-offset: 2px;
    border-radius: 8px;
  }

  /* ---- group-stage column ------------------------------------------------- */
  .group-col {
    flex: 0 0 210px;
    width: 210px;
  }
  .gs-toggle {
    display: flex;
    gap: 4px;
    justify-content: center;
    margin-bottom: 12px;
  }
  .gs-toggle button {
    flex: 1 1 0;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--muted);
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 0;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
  }
  .gs-toggle button.active {
    color: var(--on-accent);
    border-color: transparent;
    background: var(--yellow);
  }
  .gs-body {
    justify-content: flex-start;
    gap: 18px;
  }
  .gs-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .gs-head {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted-2);
    padding-bottom: 2px;
  }

  .third {
    margin-top: 28px;
  }
  .third-head {
    text-align: center;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted-2);
    margin-bottom: 8px;
  }
</style>
