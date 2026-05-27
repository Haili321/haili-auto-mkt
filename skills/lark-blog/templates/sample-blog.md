# Foo Notebook 3 Is Now Live: Faster Notes, Smarter Search

We're glad to announce that Foo Notebook 3 is now available on the Foo Platform, bringing faster local search, cross-device sync, and a refreshed sidebar to everyone on the free tier.

The change we're proudest of is search. The old indexer scanned every note on every keystroke, which kept the UI responsive only on small notebooks. Foo Notebook 3 ships a new incremental indexer that watches file changes and updates the search index in the background, so search stays under 30 ms even at 10,000 notes.

## What changed

This release focuses on three areas:

- Search: the new incremental indexer keeps results under 30 ms at notebook sizes the old version started to choke on.
- Sync: cross-device sync no longer requires the cloud sidecar; peer-to-peer over your local network is now the default.
- Sidebar: the tag panel and the recent-notes panel can be reordered, hidden, or pinned per workspace.

The full changelog is in the release notes.

*[image: search-latency-comparison.png | "Search latency before and after the incremental indexer, in milliseconds"]*

## Benchmarks

We measured search latency across three notebook sizes on a 2024-era laptop:

| Notebook size | v2 latency | v3 latency |
|---|---|---|
| 1,000 notes | 14 ms | 9 ms |
| 5,000 notes | 78 ms | 17 ms |
| 10,000 notes | 290 ms | 27 ms |

Latency includes both index lookup and result rendering. The biggest wins come from skipping disk reads for unchanged files between keystrokes.

## How to upgrade

If you're on the free tier, the update will roll out automatically over the next week. To pull it sooner:

```bash
foo notebook upgrade --channel stable
```

You can also check the current version:

```bash
foo notebook version
```

If you have an active sync session, restart the app once the upgrade finishes so the new indexer picks up the existing notebook.

> Heads up: workspaces opened in v3 are not backwards-compatible with v2. If you collaborate with someone still on v2, keep them on the same channel.

*[image: sidebar-customisation.png | "The new sidebar panel reorder UI in v3"]*

## What's next

We're working on a plugin API so third parties can ship their own sidebars and indexers. Drop into the community forum if you'd like an early look at the spec.

---

Thanks for using Foo Notebook. Feedback to feedback@example.com.
