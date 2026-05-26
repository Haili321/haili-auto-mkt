# Copy templates

Two pieces here:

1. A reference structure with placeholders, in human-readable form.
2. A worked example for a fictional product / company, as both human
   text and ProseMirror JSON, so you can adapt it field-by-field.

## Reference structure

```
📅 {Day} {DD} {Month}  ·  🕕 {HH:MM} – {HH:MM} {TZ}
📍 {Host venue} · {Floor or room} · {Street address}, {City}
🍕 {Food perk}  ·  🚨 {N} seats · {RSVP rule}

{Hook paragraph. Contrast something the audience expects against what
this event actually is. 2-3 sentences max.}

{One-line transition. E.g., "Tonight's about that second kind."}

{Host intro paragraph. Who's running this, what they're bringing, what
attendees should bring, what they'll leave with. 2-3 sentences.}

### Who should come
• {Persona 1, framed by intent: "new to X and want to build, not sit through slides"}
• {Persona 2: "tried X and hit the wall"}
• {Persona 3: "founder, engineer, PM, or just a curious builder"}
• {Persona 4: "want to meet other {city} {scene} working on X"}

### What you'll leave with
• {Concrete output: "a working X in your account, even if you've never built one"}
• {Mental model upgrade: "a better mental model for X vs Y"}
• {Community: "a few new contacts in the {city} {scene} scene"}
• {Tool fluency: "works with A, B, or C (your choice)"}

### Bring
• {Equipment, single line, with a joke or warmth: "A laptop and a charger 🔌. We've got the rest."}
• {Beginner reassurance: "First time with X? Come anyway. We'll set you up."}

### About {Product}
{Product} is {company}'s {product category}, built on a simple idea: {one-line tagline}.

{Differentiation paragraph. What's the contrast with existing options?
Reuse the product's own positioning language where it's strong; do not
invent new positioning.}

{Concrete features paragraph. 2-3 key concepts the user will actually
feel. Bold the noun phrases.}

{Implementation / compatibility paragraph. What does it run on, what
does it integrate with.}

### About {Company}
{Company} {short company description}. {1-2 sentences max, no marketing fluff.}
```

## Worked example (fictional product)

This example uses a fictional product, "Notesmith," shipped by a
fictional company, "Foo Labs." Replace these with your real product
and company names. The bold runs are marked as `**word**` for
readability; do not ship the asterisks, they are a notation artifact.

```
📅 **Wednesday 3 June**  ·  🕕 **18:30 – 21:30 BST**
📍 **Foo Labs HQ** · 6th Floor · {Street address}, {City}
🍕 Food & drinks on us  ·  🚨 **20 seats** · RSVP locks your spot

Most "personal knowledge" tools on LinkedIn are one big sidebar, one
slick demo, one happy founder typing into the void. What actually
ships is messier: notes that survive a year, link themselves to your
calendar, and remember a project you parked six months ago.

Tonight's about that second kind.

Foo Labs is bringing the team behind Notesmith, our open-source
notebook, to the City for a hands-on build night. Bring a notebook
you've been trying to tame. Leave with a working Notesmith vault.

### Who should come
• New to long-lived notebooks and want to build, not sit through slides
• Tried Obsidian or Notion and hit the wall on sync or backlinks
• Founder, engineer, PM, or just a curious builder
• Want to meet other builders working on local-first tools

### What you'll leave with
• A working Notesmith vault on your laptop, even if you've never tried local-first notes
• A better mental model for notebooks-as-files vs notebooks-as-cloud-services
• A few new contacts in the local builder scene
• Works on macOS, Linux, or Windows (your choice)

### Bring
• A laptop and a charger 🔌. We've got the rest.
• First time with markdown notebooks? Come anyway. We'll set you up.

### About Notesmith
Notesmith is Foo Labs's open-source notebook, built on a simple idea: **your notes should outlive any single app**.

Most notebooks treat each session as day one. Notesmith gives notebooks **content-addressed storage**, **calendar awareness**, and **per-vault search** across files, dates, and topics. Notes organise into topic-based stacks that survive renames. Your notebook picks up right where you left off, even after three weeks on a different project.

Notebooks also build a **link graph** between the notes you keep touching: which notes cluster together, which ones never link back, which ones haven't been opened in a year. The sidebar adjusts based on what you actually work on.

Everything is **local-first**. Swap in cloud sync, encryption, or third-party plugins without touching the core. Background jobs run on your machine and report results through the same notebook surface. Works on macOS, Linux, or Windows out of the box.

### About Foo Labs
Foo Labs builds infrastructure for tools that respect the next decade of your work, from notebooks to calendars to task systems.
```

## Same example as ProseMirror JSON

This is a full `description_mirror` document. Drop it directly into a
POST to `/event/admin/update`.

```json
{
  "type": "doc",
  "content": [
    {"type": "paragraph", "content": [
      {"type": "text", "text": "📅 "},
      {"type": "text", "text": "Wednesday 3 June", "marks": [{"type": "bold"}]},
      {"type": "text", "text": "  ·  🕕 "},
      {"type": "text", "text": "18:30 – 21:30 BST", "marks": [{"type": "bold"}]}
    ]},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "📍 "},
      {"type": "text", "text": "Foo Labs HQ", "marks": [{"type": "bold"}]},
      {"type": "text", "text": " · 6th Floor · {Street address}, {City}"}
    ]},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "🍕 Food & drinks on us  ·  🚨 "},
      {"type": "text", "text": "20 seats", "marks": [{"type": "bold"}]},
      {"type": "text", "text": " · RSVP locks your spot"}
    ]},
    {"type": "paragraph"},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Most \"personal knowledge\" tools on LinkedIn are one big sidebar, one slick demo, one happy founder typing into the void. What actually ships is messier: notes that survive a year, link themselves to your calendar, and remember a project you parked six months ago."}
    ]},
    {"type": "paragraph"},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Tonight's about that second kind."}
    ]},
    {"type": "paragraph"},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Foo Labs is bringing the team behind Notesmith, our open-source notebook, to the City for a hands-on build night. Bring a notebook you've been trying to tame. Leave with a working Notesmith vault."}
    ]},
    {"type": "paragraph"},
    {"type": "heading", "attrs": {"level": 3}, "content": [
      {"type": "text", "text": "Who should come"}
    ]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• New to long-lived notebooks and want to build, not sit through slides"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• Tried Obsidian or Notion and hit the wall on sync or backlinks"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• Founder, engineer, PM, or just a curious builder"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• Want to meet other builders working on local-first tools"}]},
    {"type": "paragraph"},
    {"type": "heading", "attrs": {"level": 3}, "content": [
      {"type": "text", "text": "What you'll leave with"}
    ]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• A working Notesmith vault on your laptop, even if you've never tried local-first notes"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• A better mental model for notebooks-as-files vs notebooks-as-cloud-services"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• A few new contacts in the local builder scene"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• Works on macOS, Linux, or Windows (your choice)"}]},
    {"type": "paragraph"},
    {"type": "heading", "attrs": {"level": 3}, "content": [
      {"type": "text", "text": "Bring"}
    ]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• A laptop and a charger 🔌. We've got the rest."}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "• First time with markdown notebooks? Come anyway. We'll set you up."}]},
    {"type": "paragraph"},
    {"type": "heading", "attrs": {"level": 3}, "content": [
      {"type": "text", "text": "About Notesmith"}
    ]},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Notesmith is Foo Labs's open-source notebook, built on a simple idea: "},
      {"type": "text", "text": "your notes should outlive any single app", "marks": [{"type": "bold"}]},
      {"type": "text", "text": "."}
    ]},
    {"type": "paragraph"},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Most notebooks treat each session as day one. Notesmith gives notebooks "},
      {"type": "text", "text": "content-addressed storage", "marks": [{"type": "bold"}]},
      {"type": "text", "text": ", "},
      {"type": "text", "text": "calendar awareness", "marks": [{"type": "bold"}]},
      {"type": "text", "text": ", and "},
      {"type": "text", "text": "per-vault search", "marks": [{"type": "bold"}]},
      {"type": "text", "text": " across files, dates, and topics. Notes organise into topic-based stacks that survive renames. Your notebook picks up right where you left off, even after three weeks on a different project."}
    ]},
    {"type": "paragraph"},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Notebooks also build a "},
      {"type": "text", "text": "link graph", "marks": [{"type": "bold"}]},
      {"type": "text", "text": " between the notes you keep touching: which notes cluster together, which ones never link back, which ones haven't been opened in a year. The sidebar adjusts based on what you actually work on."}
    ]},
    {"type": "paragraph"},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Everything is "},
      {"type": "text", "text": "local-first", "marks": [{"type": "bold"}]},
      {"type": "text", "text": ". Swap in cloud sync, encryption, or third-party plugins without touching the core. Background jobs run on your machine and report results through the same notebook surface. Works on macOS, Linux, or Windows out of the box."}
    ]},
    {"type": "paragraph"},
    {"type": "heading", "attrs": {"level": 3}, "content": [
      {"type": "text", "text": "About Foo Labs"}
    ]},
    {"type": "paragraph", "content": [
      {"type": "text", "text": "Foo Labs builds infrastructure for tools that respect the next decade of your work, from notebooks to calendars to task systems."}
    ]}
  ]
}
```

Instead of writing this JSON by hand, use `scripts/build_description.py`.

## Variants by event type

### Talk + networking event (50-100 people)

- Drop "Bring", no laptop needed, just an open mind
- Add "Speakers" heading with 🎤 emoji per speaker and a one-line bio
- Make "What you'll leave with" more about insight / inspiration than
  artifacts

### Co-working / open studio (12-25 people)

- More casual tone, can go lowercase like an after-hours invite
- Drop "Who should come", just "open door"
- Add a short agenda block with rough timestamps

### Conference / multi-day

- Add a "Schedule" heading with daily breakdown
- Keep "About" sections shorter
- The emoji header in description is less critical because Luma's own
  event UI shows day and time

### Sponsored or paid event

- Add a "Tickets" or "Pricing" heading explaining tiers
- Keep About sections proportionally larger, sponsors expect attribution
