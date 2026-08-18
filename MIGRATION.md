# Migration from runner-3 to runner-4

`runner-4` is the dedicated media/video Actions runner.

## Cutover sequence

1. Keep media engine code/configs only in `runner-4`.
2. Run `Source Ingest` with `configs/chainsaw-reze-v18d.json`.
3. Run `Render Video` using the successful ingest run ID.
4. Run `QA Video` using the successful render run ID.
5. Treat cutover as successful only if `qa_report.json` says `pass: true` and the QA contact sheets are visually acceptable.
6. After successful cutover, remove obsolete anime experiment workflows from `runner-3`.

## Phase-1 cleanup candidates in runner-3

Dedicated anime/edit experiments:

- `anime-phonk-demo.yml`
- `iphone-anime-fit-v2.yml`
- `iphone-anime-youtube-demo.yml`
- `jjk-*`
- `solo-beru-*`
- `chainsaw-*`
- `naruto-wikimedia-cc-edit.yml`
- `naruto-youtube-cc-demo.yml`
- `montagem-bandcamp-audio-test.yml`
- `pixabay-montagem-audio-test.yml`

Broader media infrastructure such as narrator benchmarks, Remotion smoke tests, R2/media bootstrap tools, WordPress media workflows and X/video utilities are not removed in phase 1 without separate review.

## Design rules

- New edit iteration = new/updated JSON config, not a new workflow.
- Runtime source/render/QA media is artifact-only and never committed.
- No workflow commits status/manifest files back to `main`.
- Heavy workflows are manual `workflow_dispatch` by default.
- Ingest, render and QA use independent concurrency groups.
