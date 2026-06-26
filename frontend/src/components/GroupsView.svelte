<script>
  let { groups = [] } = $props();
</script>

<div class="groups">
  {#each groups as g (g.name)}
    <div class="group">
      <div class="group-head">{g.name}</div>
      <table>
        <thead>
          <tr>
            <th class="pos">#</th>
            <th class="team">Team</th>
            <th>P</th>
            <th>W</th>
            <th>D</th>
            <th>L</th>
            <th>GF</th>
            <th>GA</th>
            <th>GD</th>
            <th class="pts">Pts</th>
          </tr>
        </thead>
        <tbody>
          {#each g.standings as row (row.team)}
            <tr class:adv={row.advanced}>
              <td class="pos">
                <span class="rankdot" class:adv={row.advanced}></span>{row.rank}
              </td>
              <td class="team">
                <div class="team-cell">
                  {#if row.flag_url}
                    <img src={row.flag_url} alt="" loading="lazy" />
                  {:else}
                    <span class="crest"></span>
                  {/if}
                  <span class="tname">{row.team}</span>
                </div>
              </td>
              <td>{row.played}</td>
              <td>{row.won}</td>
              <td>{row.drawn}</td>
              <td>{row.lost}</td>
              <td>{row.gf}</td>
              <td>{row.ga}</td>
              <td>{row.gd > 0 ? '+' + row.gd : row.gd}</td>
              <td class="pts">{row.points}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/each}
</div>

<style>
  .groups {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
    gap: 16px;
  }
  .group {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }
  .group-head {
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.5px;
    padding: 10px 14px;
    background-color: var(--primary-100);
    border-bottom: 1px solid var(--primary-100);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    table-layout: fixed;
  }
  th {
    color: var(--muted-2);
    font-weight: 600;
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    padding: 6px 4px;
    text-align: center;
    width: 26px;
  }
  td {
    padding: 7px 4px;
    text-align: center;
    color: var(--muted);
    border-top: 1px solid var(--border);
    width: 26px;
  }
  th.team,
  td.team {
    width: auto;
    text-align: left;
    padding-left: 12px;
  }
  th.pos,
  td.pos {
    width: 34px;
    padding-left: 10px;
    text-align: left;
  }
  td.team {
    color: var(--text);
    font-weight: 600;
  }
  .team-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    overflow: hidden;
  }
  td.team img {
    width: 20px;
    height: 14px;
    flex-shrink: 0;
    object-fit: cover;
    border-radius: 2px;
    box-shadow: 0 0 0 1px var(--border-strong);
  }
  .crest {
    width: 14px;
    height: 16px;
    flex-shrink: 0;
    background: var(--primary-100);
    border-radius: 2px;
  }
  .tname {
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  td.pts {
    color: var(--text);
    font-weight: 800;
  }
  tr.adv td {
    background: color-mix(in srgb, var(--green) 10%, transparent);
  }
  .rankdot {
    display: inline-block;
    width: 4px;
    height: 14px;
    border-radius: 2px;
    margin-right: 7px;
    vertical-align: middle;
    background: transparent;
  }
  .rankdot.adv {
    background: var(--green);
  }
</style>
