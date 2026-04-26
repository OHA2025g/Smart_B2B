/**
 * All user-visible dates on the app are shown in India Standard Time (IST, Asia/Kolkata).
 * Instants are stored/transported in UTC/ISO; formatting uses the IANA zone so the clock is
 * correct regardless of the visitor's local timezone.
 */

export const APP_TIMEZONE = 'Asia/Kolkata';
const LOCALE = 'en-IN';

function toDate(v) {
  if (v == null || v === '') return null;
  const d = v instanceof Date ? v : new Date(v);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * @param {string|number|Date} input
 * @param {Intl.DateTimeFormatOptions} [options] merged with timeZone; default: medium date + short time, 12h
 */
export function formatDateTimeIst(input, options = {}) {
  const d = toDate(input);
  if (!d) return '—';
  const { dateStyle = 'medium', timeStyle = 'short', ...rest } = options;
  return d.toLocaleString(LOCALE, { dateStyle, timeStyle, ...rest, timeZone: APP_TIMEZONE });
}

export function formatDateIst(input, options = {}) {
  const d = toDate(input);
  if (!d) return '—';
  return d.toLocaleDateString(LOCALE, { ...options, timeZone: APP_TIMEZONE });
}

export function formatTimeIst(input, options = {}) {
  const d = toDate(input);
  if (!d) return '—';
  return d.toLocaleTimeString(LOCALE, { timeStyle: 'short', hour12: true, ...options, timeZone: APP_TIMEZONE });
}

/** e.g. "Friday, 26 Apr" style bucket labels for notification lists */
export function formatLongWeekdayDateIst(input) {
  const d = toDate(input);
  if (!d) return '';
  return d.toLocaleDateString(LOCALE, {
    timeZone: APP_TIMEZONE,
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/** YYYY-MM-DD in IST; useful for stable grouping/sorting. */
export function dateKeyIst(input) {
  const d = toDate(input);
  if (!d) return '';
  return d.toLocaleDateString('en-CA', { timeZone: APP_TIMEZONE });
}
