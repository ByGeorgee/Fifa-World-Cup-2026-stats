// One-off test (no framework configured): node src/lib/bracketLayout.test.mjs
//
// Fixture is a real ESPN-derived snapshot from partway through the Round of 32 (6 matches played,
// 10 scheduled). The played matches' winner-feeder links are gone from feeds_into because ESPN
// resolved them into the next round — exactly the case that used to drop them from the bracket.
import { readFileSync } from 'node:fs';
import { computeBracketLayout } from './bracketLayout.js';

const bracket = JSON.parse(readFileSync(new URL('./__fixture_bracket.json', import.meta.url)));

let failures = 0;
function expect(label, actual, expected) {
  const ok = actual === expected;
  if (!ok) failures++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}: got ${actual}, expected ${expected}`);
}

const { columns, links } = computeBracketLayout(bracket);
const expectedCounts = {
  'round-of-32': 16,
  'round-of-16': 8,
  quarterfinals: 4,
  semifinals: 2,
  final: 1,
};

for (const col of columns) {
  expect(`${col.key} count`, col.matches.length, expectedCounts[col.key]);
}

// No round may contain duplicate matches.
for (const col of columns) {
  const ids = col.matches.map((m) => m.id);
  expect(`${col.key} unique`, new Set(ids).size, ids.length);
}

// Every PLAYED R32 match must have a connector line into the Round of 16. ESPN erases the feeder
// placeholder once a match resolves, so without reconstruction these lines go missing — the bug.
const r32 = columns.find((c) => c.key === 'round-of-32').matches;
const linkedChildren = new Set(links.map((l) => l.child));
const playedR32 = r32.filter((m) => m.status === 'final');
const playedLinked = playedR32.filter((m) => linkedChildren.has(m.id)).length;
expect('played R32 matches with a link into R16', playedLinked, playedR32.length);

// No match may feed two parents as the WINNER (guards against double-drawn lines when ESPN's
// snapshot shows a winner resolved in one slot while a stale placeholder still points at the same
// match elsewhere). A semifinal legitimately feeds the final as winner AND third place as loser,
// so only winner links are constrained to one-per-match here.
const winnerCounts = links
  .filter((l) => l.takes === 'winner')
  .reduce((acc, l) => ((acc[l.child] = (acc[l.child] ?? 0) + 1), acc), {});
const overLinked = Object.values(winnerCounts).filter((n) => n > 1).length;
expect('matches feeding more than one parent as winner', overLinked, 0);

console.log(failures ? `\n${failures} failure(s)` : '\nall passed');
process.exit(failures ? 1 : 0);
