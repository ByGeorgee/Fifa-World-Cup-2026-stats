<script>
  import { localDate, localTime } from '../lib/time.js';

  let { match, compact = false, onselect = null } = $props();

  const isLive = $derived(match.status === 'live');
  const isFinal = $derived(match.status === 'final');
  const showScore = $derived(isLive || isFinal);

  function teamLabel(slot) {
    return slot.display || slot.name || slot.short || 'TBD';
  }
</script>

<button
  class="match"
  class:compact
  class:live={isLive}
  onclick={() => onselect?.(match)}
  title="Match {match.match_number} · {match.venue?.name ?? ''}"
>
  <div class="when">
    {#if isLive}
      <span class="live-badge"><span class="dot"></span>LIVE</span>
    {:else}
      <span class="date">{localDate(match.kickoff_utc)}</span>
      <span class="time">{localTime(match.kickoff_utc)}</span>
    {/if}
  </div>

  <div class="teams">
    {#if match.official_match_number}
      <span class="matchno">Match {match.official_match_number}</span>
    {/if}
    {#each [match.home, match.away] as slot}
      <div class="team" class:winner={showScore && slot.winner} class:placeholder={slot.is_placeholder}>
        <span class="flag">
          {#if slot.flag_url}
            <img src={slot.flag_url} alt="" loading="lazy" />
          {:else}
            <span class="crest"></span>
          {/if}
        </span>
        <span class="name">{teamLabel(slot)}</span>
        {#if showScore && slot.score !== null && slot.score !== undefined}
          <span class="score" class:win={slot.winner}>{slot.score}</span>
        {/if}
      </div>
    {/each}
  </div>
</button>

<style>
  .match {
    position: relative;
    display: flex;
    align-items: stretch;
    gap: 0;
    width: 100%;
    text-align: left;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0;
    overflow: hidden;
    color: var(--text);
    transition: background 0.15s, border-color 0.15s, transform 0.15s;
  }
  .matchno {
    position: absolute;
    top: 5px;
    right: 8px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.4px;
    color: var(--muted-2);
    text-transform: uppercase;
    pointer-events: none;
  }
  .match.live {
    border-color: color-mix(in srgb, var(--live) 50%, transparent);
  }

  .when {
    flex: 0 0 52px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    padding: 8px 4px;
    border-right: 1px solid var(--border);
    background: var(--bg-2);
  }
  .date {
    font-size: 9px;
    letter-spacing: 0.5px;
    color: var(--muted);
    font-weight: 600;
  }
  .time {
    font-size: 13px;
    font-weight: 700;
    color: var(--text);
  }
  .live-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: var(--live);
  }
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--live);
    animation: pulse 1.2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .teams {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    min-width: 0;
    padding-top: 13px; /* clears the "Match N" badge in the top-right */
  }
  .team {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    min-width: 0;
  }
  .team + .team {
    border-top: 1px solid var(--border);
  }
  .team.winner .name {
    color: var(--text);
    font-weight: 700;
  }
  .team.placeholder .name {
    color: var(--muted);
    font-weight: 500;
  }

  .flag {
    flex: 0 0 auto;
    width: 20px;
    height: 14px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .flag img {
    width: 20px;
    height: 14px;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 0 1px var(--border-strong);
  }
  .crest {
    width: 20px;
    height: 14px;
    background: var(--primary-100);
    border: 1px solid var(--border-strong);
    border-radius: 2px 2px 3px 3px;
  }

  .name {
    flex: 1 1 auto;
    font-size: 12.5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text);
  }
  .score {
    flex: 0 0 auto;
    min-width: 20px;
    text-align: center;
    font-size: 13px;
    font-weight: 700;
    color: var(--muted);
    background: var(--primary-50);
    border-radius: 5px;
    padding: 1px 6px;
  }
  .score.win {
    color: var(--on-accent);
    background: var(--yellow);
  }

  .compact .when {
    flex-basis: 46px;
  }
  .compact .name {
    font-size: 11.5px;
  }
</style>
