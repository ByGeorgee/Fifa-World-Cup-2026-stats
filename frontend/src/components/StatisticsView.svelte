<script>
  let { statistics = null } = $props();
  const totals = $derived(statistics?.tournament_totals ?? null);
  const teams = $derived(statistics?.team_aggregates ?? []);
  const scorers = $derived(statistics?.top_scorers ?? []);
</script>

{#if statistics}
  <div class="stats">
    {#if totals}
      <div class="cards">
        <div class="stat-card">
          <div class="big">{totals.matches_played}</div>
          <div class="lbl">Matches played</div>
        </div>
        <div class="stat-card">
          <div class="big">{totals.total_goals}</div>
          <div class="lbl">Total goals</div>
        </div>
        <div class="stat-card">
          <div class="big">{totals.avg_goals_per_match}</div>
          <div class="lbl">Goals / match</div>
        </div>
        <div class="stat-card">
          <div class="big">{totals.teams_advanced}</div>
          <div class="lbl">Teams advanced</div>
        </div>
        {#if totals.best_attack}
          <div class="stat-card">
            <div class="big sm">{totals.best_attack.team}</div>
            <div class="lbl">Best attack · {totals.best_attack.goals} goals</div>
          </div>
        {/if}
        {#if totals.best_defense}
          <div class="stat-card">
            <div class="big sm">{totals.best_defense.team}</div>
            <div class="lbl">Best defense · {totals.best_defense.conceded} conceded</div>
          </div>
        {/if}
      </div>
    {/if}

    <div class="panels">
      <div class="panel">
        <div class="panel-head">Top scorers</div>
        {#if scorers.length}
          <ol class="scorers">
            {#each scorers as s}
              <li><span class="pname">{s.player}</span><span class="pteam">{s.team ?? ''}</span><span class="pgoals">{s.goals}</span></li>
            {/each}
          </ol>
        {:else}
          <div class="empty">No goalscorer data yet — populates as matches are played.</div>
        {/if}
      </div>

      <div class="panel">
        <div class="panel-head">Team standings (all groups)</div>
        <table>
          <thead>
            <tr><th class="l">Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr>
          </thead>
          <tbody>
            {#each teams as t}
              <tr class:adv={t.advanced}>
                <td class="l">
                  {#if t.flag_url}<img src={t.flag_url} alt="" loading="lazy" />{/if}
                  <span>{t.team}</span>
                </td>
                <td>{t.played}</td><td>{t.won}</td><td>{t.drawn}</td><td>{t.lost}</td>
                <td>{t.gf}</td><td>{t.ga}</td><td>{t.gd > 0 ? '+' + t.gd : t.gd}</td>
                <td class="pts">{t.points}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </div>
{/if}

<style>
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 14px;
    margin-bottom: 22px;
  }
  .stat-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 16px;
  }
  .big {
    font-size: 32px;
    font-weight: 800;
  }
  .big.sm {
    font-size: 18px;
  }
  .lbl {
    margin-top: 6px;
    font-size: 11.5px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .panels {
    display: grid;
    grid-template-columns: minmax(260px, 1fr) minmax(360px, 1.6fr);
    gap: 16px;
  }
  @media (max-width: 900px) {
    .panels { grid-template-columns: 1fr; }
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }
  .panel-head {
    font-weight: 800;
    font-size: 13px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--primary-100);
     background-color: var(--primary-100);
  }
  .scorers {
    list-style: none;
    margin: 0;
    padding: 6px 0;
  }
  .scorers li {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    font-size: 13px;
  }
  .scorers li + li { border-top: 1px solid var(--border); }
  .pname { flex: 1 1 auto; font-weight: 600; }
  .pteam { color: var(--muted); font-size: 11px; }
  .pgoals { font-weight: 800; min-width: 22px; text-align: right; }
  .empty { padding: 22px 16px; color: var(--muted-2); font-size: 12.5px; }

  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { color: var(--muted-2); font-weight: 600; font-size: 10.5px; text-transform: uppercase; padding: 8px 5px; text-align: center; }
  td { padding: 7px 5px; text-align: center; color: var(--muted); border-top: 1px solid var(--border); }
  th.l, td.l { text-align: left; padding-left: 14px; }
  td.l { color: var(--text); font-weight: 600; display: flex; align-items: center; gap: 8px; }
  td.l img { width: 18px; height: 13px; object-fit: cover; border-radius: 2px; }
  td.pts { color: var(--text); font-weight: 800; }
  tr.adv td { background: color-mix(in srgb, var(--green) 8%, transparent); }
</style>
