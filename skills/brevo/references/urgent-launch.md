# Urgent model-launch mode

Compose a model-launch email from official sources only (no pre-written copy
needed), build it on the template, host the image on Brevo, and send a review
test. Designed for "a new model just dropped, get an email out fast" situations.

Hard rule: this mode produces a DRAFT plus a TEST to internal reviewers. It never
sends to a real recipient list on its own. A human signs off on the test first.

## Inputs you need

Just the model name. Everything else is gathered from:
- The model vendor's official site, for capabilities, benchmarks, architecture.
- Your platform's own model page, for your pricing, any promo banner, and the
  canonical CTA url.

## Step 1: gather facts and cite them

Open both pages and pull the numbers. Keep a source next to every claim so review
is a fast spot-check:
- Vendor site: the short pitch, benchmark scores, architecture/efficiency numbers,
  context window, modality, training scale.
- Platform page: input/output/cache pricing per tier, the promo banner text (quote
  it exactly), rate limit, compatibility flags, and the model url for the CTA.

Cross-check pricing against the promo (a "50% off" banner means the listed price is
already the discounted one). Match promo wording exactly: "through <date>" is not
the same as "until <date>".

## Step 2: get a clean public image url

The header image must be a PUBLIC url with no auth/token query string.
- Good: a vendor CDN file with no `?token` query string.
- Avoid: signed/expiring urls (for example LinkedIn/licdn). Email clients block
  them, and a browser privacy guard will not even hand the url back to the agent.
- An on-page benchmark chart is often rendered as live SVG (no single image url).
  The same chart usually also exists as a flat JPEG/PNG on the vendor CDN, so list
  the page's <img> elements and pick the wide hero/benchmark file.

## Step 3: host the image on Brevo (API)

    scripts/brevo_image_import.py --url <public_image_url> --name <model>-bench

Prints a permanent img.mailinblue.com url. Use that as `header_image_url`.
(Brevo reads the format from the name, so an extension is required; the script
adds one. Max 2 MB; if the file is bigger, use a smaller CDN variant.)

## Step 4: write the copy (house style)

Structure (the template expects these fields): greeting, 1-2 intro lines, a short
heading, 4-6 plain bullets, an optional pricing block, one human closing line, a
single CTA, the sender's signature.

Style:
- Conservative claims only. State what the source supports. If the benchmark grid
  shows the model trailing on most rows, do NOT write "beats everyone"; name the
  specific wins the way a careful marketer would.
- No em dashes anywhere (the build script strips them, but write clean).
- Low AI-feel: short sentences, plain verbs (does, runs, drops into), cut hype words
  (frontier, purpose-built, dramatically, drop-in ready, from step zero). Avoid
  template-speak like "Highlights at a Glance".
- A greeting like "Hi there," and a warm one-line close read more human than "Hi!".

Put the copy into a spec JSON (see templates/model_launch_spec.example.json).

## Step 5: build the email

    scripts/build_model_email.py --spec spec.json \
        --out-html model_email.html --out-request model_request.json

Template: templates/model_launch.template.html (tokens use [[ ]] so they never
clash with Brevo's {{ contact.EMAIL }} merge tag, which stays in the footer).

## Step 6: send the review test

Send to the user and cc the reviewer. cc means you cannot use `--test-to` (it
clears cc), so put `to` and `cc` in the request JSON, keep a `TEST - ` subject
prefix, and send transactionally:

    scripts/bootstrap_runtime.sh --request-file model_request.json --send

Use the transactional path for tests to outside mailboxes. Brevo's campaign
`sendTest` only works when the recipient is already a Brevo contact, so it rejects
addresses like a personal inbox.

## Step 7 (optional): stage the real campaign as a Brevo draft

For the eventual real send to a list, create a draft campaign via the API and put
the same html on it. Default its recipients to a 0-contact placeholder list so it
cannot blast by accident; the sender sets the real list and sends from Brevo after
sign-off.

    POST /v3/emailCampaigns   {name, subject, sender, type:"classic", htmlContent,
                               recipients:{listIds:[<0-contact list>]}}
    PUT  /v3/emailCampaigns/<id>   {htmlContent}   # to update later

## Personalization (only if asked)

Most broadcasts open with a plain greeting, no name. If asked to personalize, use a
contact attribute the list actually populates, with a fallback, for example
`{{ contact.FIRSTNAME | default : "there" }}`. Confirm the field is filled on the
target list before relying on it.
