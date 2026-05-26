---
name: luma-event-promo
description: |
  End-to-end workflow for launching a polished event on Luma. Research
  comparable events in the target city, draft conversational English copy
  that doesn't read like AI slop, create the event as a Private (unlisted)
  draft via Luma's admin API, fix the time and duration traps that bite
  every first-timer, structure the description with ProseMirror headings
  and selective bold, polish theme, font, and cover photo. Trigger on
  requests like "post a workshop on luma", "make a luma event for our
  meetup", "fix the time on my luma event", or any ask that touches Luma's
  event publishing surface. Also use this when the user has an event idea
  they want help shaping into Luma-ready copy, not only when they've
  already decided to publish.
version: 0.1.0
metadata:
  requires:
    bins:
      - python3
    pip:
      - Pillow (optional, only for cover-photo padding)
    env:
      - LUMA_COOKIE (recommended) or ~/.luma_cookie
      - LUMA_EVENT_ID (optional) or ~/.luma_event_id
---

# Luma Event Promo

## What this skill is for

Launching a Luma event end-to-end without stepping on the half-dozen sharp
edges Luma's interface and API hide. The standard path:

1. Research 2-3 comparable events in the same city or scene
2. Draft conversational copy that sounds human
3. Create the event as Private (unlisted) so you can preview before sharing
4. Fix the things Luma's default Create flow gets wrong (time, duration,
   capacity)
5. Polish description structure, theme, font, cover photo

This skill captures the working recipes for each phase plus the surprises
you only learn by doing it.

## Mental model

Luma has two surfaces:

- The browser UI (`luma.com/create`, manage pages). Good for: creating
  events from scratch, picking date from the calendar, uploading images.
  Bad for: bulk edits, setting fields the UI does not expose
  (`duration_interval`, `tint_color`, `font_title`), retries after errors.
- The admin API at `https://api.lu.ma/event/admin/*`. Authenticated by
  cookies (`luma.did` + `luma.auth-session-key`). Excellent for: editing
  every field after the event exists, updating the description as
  ProseMirror JSON, fixing time bugs, swapping `cover_url` between
  existing Luma CDN images.

Cardinal rule: use the browser UI to create the event and upload images,
then use the API for everything else. Do not try to set `start_at` /
`end_at` through JS on the create form (it silently fails). Do not try
to upload images through Chrome MCP `file_upload` (it is blocked).

## When to invoke this skill

Trigger eagerly. The skill is useful whether the user is brainstorming
("we want to do a workshop in {city}, what should it look like") or
executing ("change my luma event's cover photo"). The whole pipeline
lives here.

Do not invoke for:

- Pure discovery ("what AI events are happening in {city}"). That is a
  search task, not a publishing task.
- Reading or RSVPing to an event someone else made.
- Generic copywriting unrelated to Luma.

## Phase 1: Research reference events

Before drafting copy, read 2-3 comparable events on Luma. This calibrates
tone, length, what fields hosts actually fill in, and what is currently
selling out in this city or topic.

How:

1. Open `https://luma.com/{city-slug}` (e.g., `luma.com/london`,
   `luma.com/sf`). This is Luma's city discovery page. The 8-character
   event slugs like `lk1xan1d` are in the link `href`s.
2. For each candidate, fetch the public event page HTML with your auth
   cookies and pull the description from the embedded JSON. The full
   description is in a field called `description_mirror`, sometimes also
   a literal `description` JSON string somewhere in the SSR payload.
3. The SSR HTML on `luma.com/{slug}` includes the full event JSON: name,
   `start_at`, `end_at`, capacity, `description_mirror`, location. Grep
   for `"event":\{` to find the main blob.

Look specifically at:

- Top-of-description emoji header line (date, time, location, perks,
  capacity, RSVP rule)
- Whether they include a detailed agenda or keep it loose
- "Who should come" or "This one's for you if" framing
- Sponsor / About sections at the bottom
- 1-2 well-attended events in your scene make better references than 10
  obscure ones

See `references/london-event-styles.md` for three archetypal patterns
worth studying, what works in each, and which to steal.

## Phase 2: Draft copy

Copy is where AI tells creep in fastest. Patterns to avoid:

- Em dashes (`—`). Replace with periods, colons, or restructure the
  sentence. This is the single biggest "AI wrote this" tell in English
  copy in 2026.
- "It's not just X, it's Y" sentence patterns. They are catnip for LLMs
  and readers spot them in two seconds.
- Triple-balanced lists like "shared memory, real handoffs, and the
  discipline to coordinate over weeks". One or two parallel items reads
  natural; three perfectly weighted ones reads written-by-a-bot. Break
  the symmetry by making one item longer or change its shape.
- Abstract nouns stacked: "an LLM agnostic foundation", "a community of
  builders shipping the same thing". Concrete is better: "Works with
  Claude, OpenAI, or Gemini (your choice)", "Other builders working on
  the same thing".
- "Walk in with X, walk out with Y" is fine once but has become a cliché
  in event copy. Once is enough; do not repeat the pattern.

Good signals:

- Casual contractions ("Tonight's about that second kind" beats "This
  evening is about the second kind")
- Conversational asides ("First time with agents? Come anyway. We'll
  set you up.")
- Concrete numbers and brand names instead of abstractions
- Short sentences mixed with one slightly longer one for rhythm

### Standard section structure

What works for hands-on workshops:

```
[emoji header line: date · time]
[emoji header line: venue]
[emoji header line: food perks · capacity / RSVP rule]

[hook paragraph: 1-3 sentences, contrast something the audience already
 knows with what this event actually is]

[one-line transition or summary]

[host intro paragraph: "X is bringing Y to {city} for [event type].
 Bring [input]. Leave with [output]."]

### Who should come (heading)
- 4 bullets, each starts with a verb or noun phrase naming a real persona

### What you'll leave with (heading)
- 3-4 concrete takeaways, no fluffy outcomes

### Bring (heading)
- Equipment (laptop, charger, etc.)
- Reassurance for beginners

### About [Product] (heading)
[1-3 paragraphs explaining the product. Bold the 2-3 key concept words.]

### About [Company] (heading)
[1-2 sentences max. Don't oversell.]
```

Use headings (Luma renders them clearly larger and bolder) and selective
bold on key concept words inside paragraphs. Do not use em dashes
anywhere.

See `references/copy-templates.md` for full ProseMirror JSON examples of
each section.

## Phase 3: Create the event (Private draft)

Use the browser UI. The Chrome instance must already be signed into the
Luma account that will host the event. If not, walk the user through the
Sign In flow (Google SSO is fastest if their Luma account is Google-
linked).

Steps:

1. Navigate to `https://luma.com/create`
2. Immediately change visibility from Public to Private (top-right
   dropdown). Luma's `Private` means unlisted: anyone with the link can
   register, but the event is not on any discovery surface. This is the
   right default for drafts. Do not skip this; once Public, even briefly,
   the event can be picked up by Luma's discovery crawlers.
3. Fill the title. The title field is a `<textarea>` in disguise; set it
   with JS:
   ```javascript
   const ta = Array.from(document.querySelectorAll('textarea'))
     .find(t => t.placeholder === 'Event Name');
   const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
   setter.call(ta, 'Your title here');
   ta.dispatchEvent(new Event('input', { bubbles: true }));
   ```
4. Set the date by clicking the calendar. This is critical (see Phase 4
   for why JS `setNativeValue` does not work on date fields).
5. Set times by typing into the `input[type="time"]` fields. These are
   real time inputs and JS `setNativeValue` works:
   ```javascript
   const times = document.querySelectorAll('input[type="time"]');
   const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
   setter.call(times[0], '18:30'); times[0].dispatchEvent(new Event('input', { bubbles: true }));
   setter.call(times[1], '21:30'); times[1].dispatchEvent(new Event('input', { bubbles: true }));
   ```
6. Add the location. Type a partial address into the location textarea,
   wait for Google Places suggestions, then click the right one. Do not
   pick a business-name suggestion if the building itself is in the list.
   Picking a business will leave the wrong name attached to the event.
   Pick the bare street address suggestion (`textContent` matches the
   street name plus the city on a separate line, no business name).
7. Add the "further instructions" (floor, entry directions). This is a
   separate textarea after the Places selection.
8. Add the description: click "Add Description" so the modal opens with
   the TipTap ProseMirror editor. Paste content with
   `document.execCommand('insertText', false, content)`. This preserves
   paragraph breaks. Click Done.
9. Set capacity: click the Edit pencil next to Capacity, toggle "Limit
   Event Capacity" on (use the real toggle ref, not coordinates), type
   the number, click Confirm. The Confirm button stays disabled until
   React actually registers the value change, which sometimes requires
   a real keyboard event rather than JS.
10. Click Create Event.

After Create, the event lives at `luma.com/{8-char-slug}` (the user-
facing link) and `luma.com/event/manage/evt-XXXXXXXXXXXXX` (the host
management view).

## Phase 4: Fix what Create got wrong

After Create, three things are commonly wrong.

### Wrong: the date is today (the `start_at` JS-setValue trap)

If you set the start date via JS `setNativeValue` (the obvious thing to
try since the field looks like a text input), Luma's UI displays your
typed value but its React state never accepts it. Create runs with the
default date: today.

The only reliable way to set the date through the UI is to click the
calendar popover and select the day. If you need to change the month,
click the right-chevron `.icon.animated.right` inside the calendar.
Out-of-month days at the bottom of the grid (`.day.in-active-month` from
the next month) are clickable.

If Create already ran with the wrong date, fix it via API instead of
rerunning Create:

```python
import urllib.request, json
cookie = "luma.did=...; luma.auth-session-key=usr-XXX.YYY"
body = json.dumps({
    "event_api_id": "evt-XXXXXXXXXXXXX",
    "start_at": "2026-06-03T17:30:00.000Z",
    "duration_interval": "P0Y0M0DT3H0M0S",
    "timezone": "Europe/London",
}).encode()
req = urllib.request.Request(
    "https://api.lu.ma/event/admin/update",
    data=body, method='POST',
    headers={
        "Cookie": cookie, "Content-Type": "application/json",
        "Origin": "https://luma.com",
        "Referer": "https://luma.com/event/manage/evt-XXX",
    },
)
urllib.request.urlopen(req).read()
```

### Wrong: `end_at` is `start_at` + 1h regardless of what you set

Luma controls event length via `duration_interval` (ISO 8601 duration).
If you set `end_at` directly without also setting `duration_interval`,
the API silently snaps `end_at` back to `start_at + duration_interval`.
Always set `duration_interval` explicitly.

Format: `P0Y0M0DT{hours}H{minutes}M0S`. Common values:

- `P0Y0M0DT2H0M0S`: 2 hours
- `P0Y0M0DT2H30M0S`: 2h30m
- `P0Y0M0DT3H0M0S`: 3 hours

### Wrong: capacity is unlimited

If Confirm in the capacity modal was disabled when you clicked it (it
disables itself until React sees a real keyboard event), capacity did
not save. Re-open the capacity modal, click on the number input, do
cmd+a, then Backspace, then type the number, then click Confirm. The
user might have to do this themselves if Chrome MCP keyboard events are
getting filtered.

`scripts/update_event.py` wraps the most common fixes. See the file for
a CLI.

## Phase 5: Polish

### Theme and font

Luma supports several themes (Minimal, Quantum, Warp, Emoji, Confetti).
Minimal is plain and default-ish. Quantum is a blue/purple gradient and
the most polished-looking for tech events. Warp is dark particles, very
cyber. Pick by feel.

Each theme has a default color and font you can override. From the API:

```python
{
    "event_api_id": "...",
    "tint_color": "#4ab2ea",        # accent (buttons, links)
    "font_title": "ivy-mode",       # or null for default sans-serif
}
```

Theme itself is set through the UI (Edit Event sidebar -> Appearance ->
click the theme tile). Theme cannot be set through the admin API alone.

### Cover photo

Luma's `cover_url` field stores a URL pointing to `images.lumacdn.com`.
It rejects external URLs (GitHub raw, Imgur, etc.) with a generic
upload-error message. Upload to Luma's CDN first.

Chrome MCP cannot programmatically upload files. `file_upload` returns
`Not allowed` even with valid paths. The user must upload manually:

1. Open the Change Photo modal (browser).
2. User clicks the "Drag & drop or click here to upload" zone.
3. The native macOS file picker appears outside Chrome's window (Chrome
   MCP screenshots cannot see OS UI; the user can).
4. User selects the file.
5. Luma uploads, sets `cover_url`, closes modal.

If the user's logo is not 1:1 (Luma's recommended aspect ratio), pad it
to a square first with a white or brand-colored background. PIL one-
liner:

```python
from PIL import Image
img = Image.open(src)
w, h = img.size
side = max(w, h)
new = Image.new('RGB', (side, side), (255, 255, 255))
mask = img.convert('RGBA').split()[3] if img.mode == 'RGBA' else None
new.paste(img.convert('RGBA'), ((side - w) // 2, (side - h) // 2), mask)
new.save(dst, 'PNG')
```

You can copy a `cover_url` from one event to another. Both events just
need to belong to the same Luma user or calendar that has access to that
CDN image:

```python
{"event_api_id": "evt-dest", "cover_url": "https://images.lumacdn.com/gallery-images/.../..."}
```

### Description structure (ProseMirror)

The description editor is a TipTap ProseMirror instance. When sending
via API, `description_mirror` accepts a ProseMirror document JSON.
Supported node types observed in practice:

- `paragraph` with `content: [{type: "text", text: "..."}]`
- `paragraph` with no content for empty lines
- `heading` with `attrs: {level: 3}` and a single text node
- Text marks: `[{"type": "bold"}]` on text nodes

Use `scripts/build_description.py` to build the JSON from a simpler
Python representation rather than writing nested JSON by hand. The
helper is small and easy to extend.

## Gotchas (read this before opening DevTools)

- `luma.com` and `api.lu.ma` are cross-origin from the browser's
  perspective. A `fetch('https://api.lu.ma/...', { credentials: 'include' })`
  from inside `luma.com` returns 401 because Luma's auth cookies are
  SameSite-restricted. Luma's own SPA gets around this with a same-
  origin proxy. Your code cannot. Use Python + cookies header instead.
- Chrome MCP `file_upload` tool returns `Not allowed` for any file path.
  Skip it. If you need to upload an image, hand off to the user with the
  Change Photo modal already open.
- Date field is a text-looking input but is not. Luma uses a custom date
  picker; the text representation is for display only. JS
  `setNativeValue` on it appears to succeed and the UI updates, but on
  Create the value silently reverts. Click the calendar.
- `duration_interval` is what actually controls event length, not
  `end_at`. Setting `end_at` without `duration_interval` looks like it
  works for a second then snaps back. Set both, or just set `start_at`
  + `duration_interval` and let Luma compute `end_at`.
- Em dashes are the AI tell of 2026. If you find yourself writing `—`,
  replace it. Periods, colons, or a sentence restructure are usually
  fine.
- `cover_url` only accepts `images.lumacdn.com` URLs. External URLs
  (GitHub raw, S3, etc.) return a generic upload-error and do not get
  set. Upload through the UI first to get a Luma CDN URL.
- Capacity Confirm button needs a real keyboard event to enable. JS-set
  values leave it disabled. Click the input, cmd+a, backspace, type,
  then click Confirm.
- Use Private (unlisted), not Public, while drafting. Public events can
  show up in Luma Discovery, the city page, and indexed search before
  you are ready. Private events are link-only and risk-free.
- The "Hosts" block on the event page shows the calendar avatar. To
  change it go to calendar settings, not event settings. Most users
  will not notice if you skip this; if they do, point them at
  `Settings -> Calendar -> Avatar`.

## More references

- `references/api-cheatsheet.md`: every field on `event/admin/get` and
  `event/admin/update`, with examples.
- `references/copy-templates.md`: full ProseMirror description JSON for
  a hands-on workshop, ready to adapt.
- `references/london-event-styles.md`: three archetypal patterns worth
  studying, what to steal from each.
- `references/gotchas.md`: extended notes on the gotchas above, with
  dead-ends tried.
- `scripts/update_event.py`: CLI to update fields on an existing event
  via API.
- `scripts/build_description.py`: helper to build ProseMirror
  description JSON from a clean Python representation.
