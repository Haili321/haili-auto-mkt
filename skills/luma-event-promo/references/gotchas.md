# Gotchas

Extended notes on the things that went wrong, the dead-ends that were
tried, and what actually works.

## 1. The date field looks like a text input but is not

Symptom: You set the start date through JS:

```javascript
const ta = document.querySelector('input[value="Tue 19 May"]');
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(ta, 'Tue 2 Jun');
ta.dispatchEvent(new Event('input', { bubbles: true }));
ta.dispatchEvent(new Event('change', { bubbles: true }));
ta.dispatchEvent(new FocusEvent('blur', { bubbles: true }));
```

The UI updates and shows "Tue 2 Jun". You click Create Event. The
created event is on the original date (today), not June 2.

Why: Luma's date input is a custom React date picker. The visible
`<input type="text">` is a display proxy. React state stores the date as
a Date object via the calendar picker; the displayed text is rendered
from React state, not the other way around. Your value-set event makes
the displayed text wrong, but React state never updated. On submit, the
React state wins.

Fix: Don't use JS for date. Click the calendar:

```javascript
// Open calendar popover
document.querySelector('input[value^="Tue"]').click();

// Go to next month if needed
document.querySelector('.icon.animated.right').click();

// Click the target day (must be in active month, not the dimmed
// prev/next month overflow)
const target = Array.from(document.querySelectorAll('.day'))
  .find(d => d.textContent.trim() === '2'
             && d.className.includes('in-active-month')
             && !d.className.includes('disabled'));
target.click();
```

Workaround if Create already ran with the wrong date: use the API
instead of recreating. POST `/event/admin/update` with `start_at` and
`duration_interval`. See SKILL.md Phase 4.

Dead-end tried: Dispatching keyboard events on the input to simulate
typing. The input does not accept typed input as a parse source. The
only way to update React state is the calendar component itself.

## 2. `end_at` silently snaps to `start_at` + `duration_interval`

Symptom: You POST `/event/admin/update` with
`start_at: "2026-06-02T17:30:00.000Z"` and
`end_at: "2026-06-02T20:30:00.000Z"`. The response shows
`end_at: "2026-06-02T18:30:00.000Z"`, one hour after start, not three.

Why: Luma stores event length as `duration_interval` (ISO 8601
duration). `end_at` is computed server-side from
`start_at + duration_interval`. If you do not send `duration_interval`,
it keeps the existing value (which on a freshly-created event is 1 hour
by default).

Fix: Always send `duration_interval` when you change times:

```python
{
    "event_api_id": "...",
    "start_at": "2026-06-02T17:30:00.000Z",
    "duration_interval": "P0Y0M0DT3H0M0S",
    "timezone": "Europe/London",
}
```

You do not need to send `end_at` at all. Luma computes it.

Dead-end tried: Setting `end_at` only (no `start_at` change), still
snapped back to start + existing duration.

## 3. Chrome MCP `file_upload` returns "Not allowed"

Symptom: You call `mcp__Claude_in_Chrome__file_upload` with a real
`<input type="file">` ref and a valid absolute path on the local
machine. Response: `{"code":-32000,"message":"Not allowed"}`.

Why: Best understanding is this is a deliberate security boundary in
the Chrome extension that backs the MCP. It does not let the
controller agent push arbitrary local files into web pages without
the user's explicit drag-drop or file-picker interaction.

Workaround: Hand off to the user. Open the Change Photo modal (or
whatever upload UI), then tell the user to click the upload zone
themselves. The native macOS file picker appears outside Chrome's
drawing area, invisible to Chrome MCP screenshots but visible to the
user. They pick the file. Luma uploads.

If the file is not already in a convenient location, save it to
`~/Desktop` or `~/Downloads` first so the user does not have to
navigate Finder.

Dead-end tried:

- Different absolute paths (Desktop, Downloads, /tmp, /var/...): all
  rejected.
- Using `computer-use` mcp's `left_click` on the upload button: the
  native file picker opens but `computer-use` cannot see it either (OS
  UI is filtered). The user can interact with it though.
- Trying to set `<input type="file">.files` via JS: blocked by browser
  security (FileList objects can only be set by user actions).

## 4. Cross-origin fetch from `luma.com` to `api.lu.ma` returns 401

Symptom: In a `javascript_exec` on `luma.com`, you call:

```javascript
fetch('https://api.lu.ma/event/admin/get?event_api_id=...', { credentials: 'include' })
```

Response: 401 `{"message":"You are not signed in."}`.

But Luma's own SPA on the same page successfully calls `api.lu.ma`.
How?

Why: Luma's auth cookies are SameSite-restricted. `luma.com` and
`api.lu.ma` are different sites by browser SameSite rules, so cross-site
fetch does not carry the cookies. Luma's SPA almost certainly uses a
same-origin proxy (probably the Next.js BFF layer in `luma.com/api/*`)
that forwards to `api.lu.ma` server-side, so from the browser's
perspective the requests are same-origin.

Workaround: Don't try to call `api.lu.ma` from in-browser JavaScript.
Call it from a Python script with the user's cookies in the `Cookie`
header. That is how this skill does it.

Dead-end tried: Adding `mode: 'cors'`, adding custom headers
(`X-Luma-Client-Type: luma-web`), changing referrer policy. None work.
The cookies just are not sent.

## 5. `cover_url` rejects external URLs

Symptom: You POST `cover_url: "https://raw.githubusercontent.com/.../logo.png"`
to `/event/admin/update`. Response: 400
`{"message":"That image didn't upload properly. Please try again."}`.

Why: Luma validates that `cover_url` points to `images.lumacdn.com`.
External hosts are rejected, even if reachable.

Fix: Upload the image to Luma's CDN first (through the UI), then update
`cover_url` to the resulting `images.lumacdn.com` URL. You can later
read another event's `cover_url` and reuse it across events you
control; Luma's CDN URLs do not appear to be access-controlled beyond
knowing the URL.

Dead-end tried:

- POST to `/image/upload`, `/upload`, `/event/admin/upload-cover`,
  `/files/upload`: all 404.
- Hijacking `window.fetch` in `luma.com` to capture the SPA's upload
  request: did not trigger because Chrome MCP cannot drive the upload
  UI to fire it.

## 6. Title field is a textarea, not an input

Symptom: You query
`document.querySelector('input[placeholder="Event Name"]')` and get
null. The visible Event Name field does not appear in any input lookup.

Why: Luma renders the title field as `<textarea>` so it can wrap to
multiple lines as the user types a long title. It is styled to look
like a single-line input.

Fix:

```javascript
const ta = Array.from(document.querySelectorAll('textarea'))
  .find(t => t.placeholder === 'Event Name');
```

JS `setNativeValue` works on this one (unlike the date field), it is a
standard controlled textarea.

## 7. Capacity Confirm button stays disabled after JS-set value

Symptom: You toggle "Limit Event Capacity" on, set the Max Capacity
input value to 20 via JS, click Confirm. Confirm appears greyed out and
nothing happens.

Why: Luma's React state for the capacity modal tracks "has the user
actually edited this since opening". JS `setNativeValue` does not
count. Confirm only enables after a real user keyboard event in the
input.

Fix: Use real keyboard events:

```javascript
// Click on the input first to focus
inputRef.click();
// Select all, delete, then type, like a real user
// (chrome MCP `computer` tool with `triple_click` + `type` works)
```

Or just have the user do this step themselves if Chrome MCP keyboard
events get filtered.

## 8. Place autocomplete picks businesses by default

Symptom: You type "{street address}, {city}" in the location field, see
a list of suggestions, click the first one. The selected location shows
up as some business name with the address attached, not what you
wanted.

Why: Google Places returns businesses at that address in addition to
the bare address. Luma's React UI sometimes selects the first item with
a JS `.click()` regardless of which one is the building.

Fix: Programmatically find the option whose `textContent` is only the
street name and city (no business name):

```javascript
const target = Array.from(document.querySelectorAll('div'))
  .find(d => d.textContent.trim() === '{STREET ADDRESS}{CITY}'
             && d.children.length === 1);
target.click();
```

(The lack of comma between street name and city is because the two
lines are separate text nodes with no comma separator in the DOM.)

If the wrong place was already selected, click the X button on the
location card and type again. The X button position is roughly at
`(modalRight - 30, locationCardY)` if `find` is not picking it up.

## 9. Description preview shows skeleton briefly after API update

Symptom: You POST a description update via API, refresh the event page,
the "When & Where" / "About Event" sections briefly show grey skeleton
loaders instead of content.

Why: Luma's cache invalidation between API write and SSR read is
eventually consistent. Usually resolves in 2-5 seconds.

Fix: Tell the user to refresh again or wait a few seconds. Do not panic
and re-POST.

## 10. Em dashes in your draft are a tell

Symptom: The user reads your first draft and says it reads like
ChatGPT wrote it, or asks you to remove the dashes.

Why: ChatGPT and similar models have heavy training bias toward em-
dash-separated parenthetical phrases ("A — B —"). Editors and writers
in 2026 spot them in two seconds. Other tells in the same family:
"It's not X, it's Y" parallel structure, three-balanced lists, abstract
noun stacks ("a community of builders shipping the same thing").

Fix:

- Replace `—` with periods, colons, or restructured sentences.
- Break perfectly balanced lists. Make one item longer or change its
  shape.
- Swap abstract nouns for concrete examples or brand names.
- Use contractions ("Tonight's" not "This evening is").
- Mix short and longer sentences for rhythm.

See "Phase 2: Draft copy" in SKILL.md for the full list and good
signals to aim for.

## 11. Image aspect ratios

Symptom: You upload a beautifully-designed landscape 3:2 logo as the
cover. Luma displays it as a 1:1 square and crops out the right third
(where the brand name lives).

Why: Luma's cover photo is rendered as a 1:1 square on event pages.

Fix: Pad your image to 1:1 before uploading. With Python:

```python
from PIL import Image
img = Image.open(src)
w, h = img.size
side = max(w, h)
new = Image.new('RGB', (side, side), (255, 255, 255))  # or brand color
mask = img.convert('RGBA').split()[3] if img.mode == 'RGBA' else None
new.paste(img.convert('RGBA'), ((side - w) // 2, (side - h) // 2), mask)
new.save(dst, 'PNG')
```

For brand color background, replace `(255, 255, 255)` with your
brand's RGB tuple.

## 12. Sessions do not survive across browser profiles

Symptom: User says "I'm logged in to luma" but the Chrome MCP-controlled
browser shows "Sign In". The user's regular Chrome and Chrome MCP's
Chrome are separate profiles.

Fix: Sign in to the target account in the Chrome MCP browser
explicitly. Do not assume cookies transfer between profiles. Once
signed in, the session persists for that profile.

## 13. Cookies and passwords in chat are a leak

Symptom: User pastes their Luma password or cookies in chat to give the
skill access.

Why: Cookies and passwords in chat history persist in the conversation
and (depending on backend) may be retained.

Fix:

- Use the cookies for the current task, but recommend the user
  terminate their Luma session afterward (Settings -> Sessions -> Log
  out all sessions) and / or change the password if they shared it.
- Do not echo the credentials back unnecessarily.
- If you need to call the API multiple times, store the cookies in a
  variable, not in shell history that could be saved.
