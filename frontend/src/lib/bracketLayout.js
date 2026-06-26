// Pure layout ordering for the knockout bracket, extracted from BracketView so it can be tested.
//
// Each round is ordered so that the two matches feeding a given next-round match sit adjacent
// (post-order DFS from the final). This lays the columns out as a left-to-right pyramid.

export const ROUND_ORDER = ['round-of-32', 'round-of-16', 'quarterfinals', 'semifinals', 'final'];

export function computeBracketLayout(bracket) {
  if (!bracket) return { columns: [], third: null };

  const byId = {};
  for (const r of bracket.rounds) for (const m of r.matches) byId[m.id] = { ...m, round: r.key };

  const childOf = {}; // parentId -> { home, away } feeding-match ids
  const linkedChildren = new Set(); // matches already feeding a parent (each feeds exactly one)
  for (const r of bracket.rounds)
    for (const m of r.matches)
      for (const fi of m.feeds_into)
        if (fi.takes === 'winner') {
          (childOf[fi.match_id] ??= {})[fi.slot] = m.id;
          linkedChildren.add(m.id);
        }

  // Reconstruct links lost to result resolution. Once a match is final, ESPN replaces the
  // "Round of N M Winner" placeholder in the next round with the actual qualified team, so the
  // feeder reference (and thus feeds_into) disappears. Re-derive each missing link by matching a
  // resolved slot to the prior-round match its team won. Restricted to the immediately preceding
  // round so a team that keeps winning maps to the correct feeder at each step.
  const roundIndex = {};
  ROUND_ORDER.forEach((rk, i) => (roundIndex[rk] = i));
  const winnerByRoundTeam = {}; // `${roundIdx}:${teamId}` -> match id
  for (const r of bracket.rounds) {
    const ri = roundIndex[r.key];
    if (ri == null) continue;
    for (const m of r.matches)
      for (const slot of ['home', 'away'])
        if (m[slot]?.winner && m[slot]?.team_id) winnerByRoundTeam[`${ri}:${m[slot].team_id}`] = m.id;
  }
  for (const r of bracket.rounds) {
    const ri = roundIndex[r.key];
    if (ri == null || ri === 0) continue;
    for (const m of r.matches)
      for (const slot of ['home', 'away']) {
        if (childOf[m.id]?.[slot]) continue; // live feeder link still present
        const tid = m[slot]?.team_id;
        if (!tid) continue;
        const child = winnerByRoundTeam[`${ri - 1}:${tid}`];
        // Skip if this match already feeds a parent via a live placeholder elsewhere — ESPN's
        // mid-update snapshots can briefly show a winner resolved in one slot while the stale
        // placeholder still stands in another; trust the explicit link and never feed two parents.
        if (!child || linkedChildren.has(child)) continue;
        (childOf[m.id] ??= {})[slot] = child;
        linkedChildren.add(child);
      }
  }

  const orderByRound = {};
  const seen = new Set();
  function visit(id) {
    const m = byId[id];
    if (!m || seen.has(id)) return;
    seen.add(id);
    const kids = childOf[id];
    if (kids?.home) visit(kids.home);
    if (kids?.away) visit(kids.away);
    (orderByRound[m.round] ??= []).push(id);
  }
  visit('final');

  const columns = ROUND_ORDER.map((rk) => {
    const r = bracket.rounds.find((x) => x.key === rk);
    if (!r) return null;
    // DFS order for matches reachable from the final; then append any not reached (e.g. a played
    // match whose winner couldn't be traced forward) in their natural order so none are dropped.
    const ordered = orderByRound[rk] ?? [];
    const inOrder = new Set(ordered);
    const ids = [...ordered, ...r.matches.map((m) => m.id).filter((id) => !inOrder.has(id))];
    return { key: rk, label: r.label, matches: ids.map((id) => byId[id]).filter(Boolean) };
  }).filter(Boolean);

  // Connector links for drawing: { child, parent, slot }. Winner links come from the merged
  // childOf (live feeders + the ones reconstruction recovered for played matches); loser links
  // (e.g. semifinal loser -> third place) are taken straight from live feeds_into.
  const links = [];
  for (const [parent, kids] of Object.entries(childOf))
    for (const slot of ['home', 'away'])
      if (kids[slot]) links.push({ child: kids[slot], parent, slot, takes: 'winner' });
  for (const r of bracket.rounds)
    for (const m of r.matches)
      for (const fi of m.feeds_into)
        if (fi.takes !== 'winner')
          links.push({ child: m.id, parent: fi.match_id, slot: fi.slot, takes: fi.takes });

  const third = bracket.rounds.find((x) => x.key === 'third-place') ?? null;
  return { columns, third: third?.matches?.[0] ?? null, links };
}
