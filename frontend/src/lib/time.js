// Format a stored UTC ISO timestamp into the viewer's local timezone.

export function localDate(utc) {
  if (!utc) return '';
  // e.g. "30 JUN" (day-first, matching the reference layout regardless of locale order)
  const d = new Date(utc);
  const day = d.toLocaleDateString(undefined, { day: '2-digit' });
  const mon = d.toLocaleDateString(undefined, { month: 'short' }).toUpperCase();
  return `${day} ${mon}`;
}

export function localTime(utc) {
  if (!utc) return '';
  // e.g. "00:30"
  return new Date(utc).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function localTimeZoneLabel() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return 'local';
  }
}
