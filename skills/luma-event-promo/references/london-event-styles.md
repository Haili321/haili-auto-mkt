# Event style reference

Notes on three archetypal patterns worth studying on Luma city pages
before drafting your own event. The point is calibration: what do
successful hosts actually write, what fields do they fill, what tone
hits the target audience.

## How to do this research yourself

1. Open `https://luma.com/{city-slug}` (e.g., `luma.com/london`,
   `luma.com/sf`, `luma.com/nyc`). It lists ~50-100 upcoming events.
2. In the page DOM, all event short links match `^/[a-z0-9]{4,10}$`.
   Filter for events with names containing keywords relevant to your
   audience ("AI", "agent", "workshop", "build", "hack").
3. Fetch each event page via `curl` with your auth cookies. The full
   description is embedded in the SSR HTML:
   ```bash
   curl -s -H "Cookie: luma.did=...; luma.auth-session-key=..." \
        "https://luma.com/{slug}" \
        | python3 -c 'import sys, re, json; html = sys.stdin.read();
   matches = re.finditer(r"\"description(?:_text|_md|_mirror)?\"\s*:\s*\"((?:[^\"\\\\]|\\\\.)*)\"", html)
   for m in matches:
       raw = m.group(1)
       if len(raw) > 200:
           print(json.loads("\"" + raw + "\"")[:3000])'
   ```
4. Pick 2-3 events that look closest to what you want to build and read
   them carefully.

Three archetypes useful for AI / tech workshops, with what works in
each:

## Archetype 1: Sponsor-led build-along (~100 attendees, 3-4 hours)

Shape: vendor or community hosts a hands-on workshop with one strong
positioning hook and an explicit "bring a real problem" framing.

What works in the copy:

- Opening hook with contrast. Three lines, each tighter than the last,
  escalating from setup to call-to-action.
- "Bring a real problem" as an invitation. Forces attendees to come
  with something concrete instead of just listening.
- No detailed agenda timestamps when it is a build-along (not a talk).
  Skipping the agenda keeps it loose.
- About Sponsor block at the end. Structure: one sentence positioning
  + one paragraph credibility (customer logos, traction signals).

Steal: the "Bring a real problem" framing, the three-line escalating
hook, the About Sponsor block placement.

Do not steal if your audience is broader than founders: the founder-
focused framing leaves out engineers / PMs / curious builders.

## Archetype 2: Curated speaker night (~120 attendees, 3 hours, often sells out)

Shape: invite-list event with 2-3 named speakers, food, networking, run
by a community or company that wants both attendees and recruits.

What works in the copy:

- Top emoji header line in one row:
  `📅 Date | 🕕 Time | 📍 Venue | 🍕 Food perks | 🚨 RSVP rule`.
  Everything an attendee needs to commit or decline in one glance.
- Punchy hook that sets expectations: contrast a "polished" version
  of the topic that lives on LinkedIn against the "real" version this
  event will cover.
- Speakers block with one line of bio per name. The bios are
  specific ("Founding engineer at X, ex-Y") not generic ("expert in
  AI"). Specificity sells the credential.
- Detailed agenda with timestamps. Useful for an event with talks
  because attendees can plan arrival.
- "This one's for you if" bullet block, 4-5 bullets each starting with
  "You're" or "You want". Reads like the host is talking directly to a
  specific reader.
- Recruiting hook at the end. Soft pitch that does not feel like one
  because it follows the value: "If you find yourself thinking 'wait,
  I want to work here'..."
- About blocks for both host community and sponsor / venue. Two
  paragraphs max each.

Steal: emoji header line format, "polished vs real" hook, "This one's
for you if" framing, soft hiring hook embedded in About Sponsor.

## Archetype 3: Casual co-working / open studio (~100-130 attendees, 4-6 hours)

Shape: lowercase, builder-tribe tone. Recurring weekly or monthly
slot. Permissive agenda: "come when you can".

What works in the copy:

- All-lowercase casual tone. Reads like a Discord message, not a
  corporate event. Fits the audience (founders, hackers).
- Direct, almost terse language. "every friday in {city}, founders and
  builders bring laptops, work on the thing they actually need to
  ship, show what moved, and talk through blockers. now we are
  bringing that format to {new city}."
- Concrete agenda with rough timestamps. "4pm grab a seat and co-work
  / 7pm intros (30s each) / until 11pm co-work, mingle and help each
  other". The "rough" matters: it is permission to come and go.
- Sponsors listed as one-line descriptions. "extended: unified margin
  trading across crypto..." Tells attendees who is funding this
  without making them click anything.
- CTA for community involvement at the end. "we want this to become
  a real weekly event. if you want to help host it long-term..."

Steal: the lowercase casual tone (when it fits your audience), the
short-sentence rhythm, the rough / permissive agenda format, the "want
to help host?" community CTA.

Do not steal: long sessions (6 hours) are unusual; only do this when
it really is a co-working format. Most events should be 2-3 hours.

## Patterns that show up across all three archetypes

- Top emoji header line. Adopted by roughly 80% of well-attended tech
  events. Even when the event also has a detailed agenda elsewhere,
  the top emoji line is the at-a-glance summary attendees rely on.
- "What you'll leave with" or equivalent. Concrete outcomes. Hosts who
  promise specific takeaways get more registrations than hosts who
  promise inspiration.
- About blocks at the bottom. Two is the norm: About Host + About
  Sponsor / Product, or About Host + About Featured Speaker.
- Conversational hooks. Almost nobody opens with "Join us for an
  evening of...". The good ones open with a contrast or a problem.
- Beginner reassurance. Events with ~30-50% beginner attendance always
  have one explicit line: "Beginners welcome", "First time? Come
  anyway", "No experience needed". Events that do not say this often
  skew advanced.

## Patterns that mark an event as "from a corporate marketing team"

These tend to underperform:

- Long paragraph at the top with no formatting
- Phrases like "this evening promises to be an unforgettable
  opportunity to..."
- Three speakers with three-paragraph bios each (the user reads zero
  of them)
- No specific outcomes; "you'll leave inspired"
- Generic stock-photo cover

If you are writing for a brand that has marketing copy from their PR
team, gently steer them toward the patterns above. It is a tone shift,
not a content shift.

## When the patterns above will not transfer

Other cities have their own tonal norms:

- SF / NYC: more startup vocabulary, more "find your tribe" phrasing,
  slightly more emoji-heavy.
- Berlin / Amsterdam: more bilingual events, less emphasis on title-
  driven hooks, more emphasis on practical workshop content.
- Singapore / Tokyo / HK: similar structure but copy tends to be more
  formal. Watch the emoji density.

When you do the research step for a city you have not worked in, spend
extra time reading the well-attended events to recalibrate.
