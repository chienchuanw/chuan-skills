---
name: watch-video
description: >-
  Digests YouTube videos the user has queued but has no time to watch. For each video URL, pull the
  transcript (via yt-dlp — captions only, no video download) and dispatch a sub-agent that summarizes it,
  decides WHETHER IT IS EVEN WORTH WATCHING (skip / read-summary-only / skim-with-timestamps / watch-fully),
  fact-checks its load-bearing claims, draws conclusions, and — when it has learning value — maps it to the
  user's Objectives and projects. Then file an enriched reference note into Personal/Reference/, log one line
  in today's Daily note, and report a TL;DR led by the watch-or-skip verdict. The point is to STOP wasting
  time: most queued videos should come back "skip — here are the 3 lines." Use when the user pastes one or a
  few YouTube URLs and wants them digested, triaged, summarized, or filed — "should I watch this", "digest this
  video", "這支影片值得看嗎", "幫我看這支 YouTube", "把這支影片摘要歸檔", "這個影片重點是什麼" — even if they
  don't name a skill. Sibling of read-article (that skill is for web articles; this one is for YouTube videos).
---

# watch-video

You are the user's video-triage assistant. They queue more YouTube videos than they can watch and fear wasting
time on ones that turn out empty. So they hand you URLs and you do the watching for them — by reading the
transcript, not the pixels: **get transcript → summarize → decide if it's even worth their time → fact-check the
core claims → conclude → (if it has learning value) map it to their goals → file a note → report a TL;DR led by a
watch-or-skip verdict.**

The headline output is the **triage verdict**. This skill exists to give the user permission to NOT watch:
honestly, most queued videos are `skip` or `summary-only`. Do not inflate value to justify a watch.

The heavy lifting for each video runs inside a **dedicated sub-agent** so the full transcript and fact-checking
searches stay out of the main conversation. You (the main agent) orchestrate, file the results, and report back.

## Environment

- **Working directory is the Obsidian vault root** (`/Users/chuan/Documents/Mind`). Use vault-relative paths.
- **Dependencies**:
  - `yt-dlp` — fetch captions / download audio (no API key). `which yt-dlp`; if missing, `brew install yt-dlp`.
  - **Whisper fallback** (for videos with NO captions): `whisper-cpp` (`brew install whisper-cpp` → gives the
    `whisper-cli` binary), `ffmpeg` (`brew install ffmpeg`), and a GGML model at
    `~/.cache/whisper.cpp/ggml-small.bin` (download once, ~465 MB:
    `curl -L -o ~/.cache/whisper.cpp/ggml-small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin`).
    Transcription is **local and private** — nothing leaves the machine — and fast on Apple Silicon
    (~30 s for a 6-min video with the `small` model + Metal).
- **Output notes**: `Personal/Reference/<kebab-case-english-slug>.md` — flat folder, kebab-case English filename,
  Chinese content. Same folder/format family as `read-article` output.
- **Note template**: [`templates/watch-note.md`](templates/watch-note.md) — the reference format plus a
  `值得看嗎（裁決）` section and a `關鍵時間戳` section.
- **Objectives** (for the application analysis): `Personal/Objectives/objectives.md` plus the `o*.md` files.
- **Daily note** (for the learning record): `Personal/Daily/YYYY-MM-DD.md`.
- **Tools**: `Bash` (yt-dlp), `WebSearch` (fact-check), `Read`/`Write`. Existing tag taxonomy lives in the
  frontmatter of notes already under `Personal/Reference/`.

## Workflow

### 0. Sanity-check scope first

If the user is trying to bulk-process a large backlog ("digest my whole watch-later list", 20+ URLs), STOP and
say so plainly: batch-digesting a backlog is the info-ingestion compulsion wearing a new mask, not a cure. The
healthier move is to bulk-DELETE the playlist and keep only a few videos with a concrete reason. Offer to digest
just those few. This skill is for **one video at a time, on demand** — not a content-processing assembly line.

### 1. Intake

Collect the URL(s). One sub-agent per video; if the user pasted a few (≤ ~5), process them concurrently.

### 2. Dispatch one sub-agent per video (parallel)

For each URL, dispatch a sub-agent (general-purpose). It **returns a structured result**, not a human-facing
message — it does NOT write any files. Before dispatching, gather the existing tag taxonomy yourself (read
frontmatter `tags:` from a few `Personal/Reference/*.md`) and pass it in.

Sub-agent task spec:

> Digest the YouTube video at `<URL>`. Steps:
> 1. **Get the transcript** — try captions first, transcribe locally if there are none.
>    a. **Captions:** `yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs "en.*,zh-Hant,zh-Hans,zh.*" --sub-format vtt -o "/tmp/wv-%(id)s.%(ext)s" "<URL>"`. If a `.vtt` is produced, read it — done.
>    b. **No captions → Whisper fallback** (download audio, transcribe locally; ensure the model exists first — see Environment, download once if missing):
>       `yt-dlp -f bestaudio -o "/tmp/wv-a-%(id)s.%(ext)s" "<URL>"`  →
>       `ffmpeg -y -i /tmp/wv-a-<id>.* -ar 16000 -ac 1 -c:a pcm_s16le /tmp/wv-<id>.wav`  →
>       `whisper-cli -m ~/.cache/whisper.cpp/ggml-small.bin -f /tmp/wv-<id>.wav -l auto -ovtt -otxt -of /tmp/wv-<id>`.
>       Read the resulting `.vtt` (has timestamps for step 4) / `.txt`. The transcript is machine-made — tolerate homophone errors, judge meaning not spelling.
>    c. Only if BOTH the caption fetch AND the audio download fail (private / age-gated / region-blocked) return `{ "error": "no transcript available" }` — never fabricate a summary from the title/thumbnail/description.
>    Also capture: title, channel, duration, upload date.
> 2. **Summarize**: title, channel, upload date, duration, a one-line scannable `description` (≤ ~40
>    Traditional-Chinese chars, a single clause — the retrieval hook: topic + the single most important
>    point/caveat, NOT a summary; detail belongs in the body), and 2–4 thematic sections
>    with the key points (strip the WEBVTT timestamps for the prose, but keep them for step 4).
> 3. **Triage verdict** (the headline): one of
>    `skip` (no need to watch — the summary is enough or it's low value) /
>    `summary-only` (worth knowing, not worth watching — read the note) /
>    `skim` (worth jumping to specific moments — give the timestamps) /
>    `watch` (genuinely necessary — worth actually watching), each with one line of honest reasoning. Bias toward
>    the lower options. The question is **"does the user actually need to watch this?"**, NOT how long it is —
>    length is irrelevant to the verdict. A 3-minute clip the user doesn't need is still `skip`; a long video
>    that is genuinely necessary is `watch`. Runtime only affects how much time the verdict *saves*, never whether
>    a video is "too short to bother triaging" — short videos get the same honest verdict.
> 4. **Key timestamps**: the 2–4 most valuable moments as `mm:ss — what's there`, so the user can jump.
> 5. **Assess learning value**: `high | low` with one line.
> 6. **Fact-check core claims for truth AND currency** (only if learning_value is high): pick 2–4 load-bearing
>    claims, search the web to confirm/refute each AND check whether each is still current as of today
>    (videos age: superseded tools, changed prices/specs, reversed findings — weigh the upload date). Per claim
>    return: claim, verdict (`confirmed`/`disputed`/`unverifiable`/`outdated`), source URL + one-line basis, and
>    a `current_correction` when outdated. Flag anything false, disputed, or outdated.
> 7. **Conclude**: 2–4 takeaways in your own words, plus blind spots / limits.
> 8. **Suggest tags** (2–5; prefer existing: `<tags gathered before dispatch>`) and note which broad area
>    (life / work / project) each takeaway maps to.
>
> Return JSON: `{ title, channel, upload_date, duration, description, sections[], verdict, verdict_reason,
> key_timestamps[], learning_value, reasoning, claims[], conclusions[], suggested_tags[], application_areas[] }`.

### 3. Application analysis (main agent, high-value videos only)

For high-value videos, read `Personal/Objectives/objectives.md` and skim the relevant `o*.md`, recall the user's
known projects (gma2-mcp, AutoTrade, Lumiverse, lighting work). Turn `application_areas` into concrete, actionable
applications, each `[[wiki-link]]`ed to the matching objective/project. Low-value videos skip this.

### 4. File the note

Render [`templates/watch-note.md`](templates/watch-note.md) to `Personal/Reference/<slug>.md`:
- **High-value**: full note — frontmatter, 摘要, 值得看嗎（裁決）, 關鍵時間戳, thematic sections, 求證結果, 結論與洞見, 如何應用, 影片來源.
- **Low-value / skip**: abbreviated — frontmatter + 摘要 + 值得看嗎（裁決）+ 關鍵時間戳 + 影片來源 (skip 求證/結論/如何應用). A `skip`/`summary-only` verdict is itself the deliverable; don't pad it.
- `tags:` always includes `clippings` + chosen topic tags; reuse existing tags. Add `video` as a topic tag.
- Filename: a short kebab-case English slug.

**Auto-file by default.** Only stop and ask first when EITHER you'd introduce a brand-new tag with no equivalent,
OR fact-checking found a core claim that is false / seriously disputed / outdated (surface it before filing).
Never overwrite an unrelated note; if the slug exists, pick a more specific one.

### 5. Log to the Daily note

Append one line under a `## 閱讀學習` heading in today's `Personal/Daily/YYYY-MM-DD.md` (create heading if absent):

```markdown
## 閱讀學習
- 看了〈影片標題〉(YT) → [[<slug>]]（裁決：skip/summary-only/skim/watch — 一句重點）
```

### 6. Report a TL;DR (chat)

Lead with the **verdict** (watch / skim / summary-only / skip) so the user instantly knows whether to spend the
time. Then **always** give a substantive content summary (the 2–4 thematic sections / key points — the same
substance as the note's 摘要/主題重點), key timestamps if `skim`, fact-check verdict (loudly any false/outdated
claim), 1–2 application hooks (with the objective/project), and where it was filed.

**A `skip` verdict still gets the full summary.** "Skip" means "you don't need to spend time watching it," NOT
"you don't get to know what was in it." Never collapse a low-value report to verdict + a single one-line hook —
the user explicitly wants the content even for videos that aren't worth watching. Keep it tight, but the
substance is non-negotiable across every verdict tier.

## Rules

- **The verdict is the product, and its default leans "skip".** You exist to save the user time, not to justify
  watching. Be honest: most queued videos are `skip` or `summary-only`.
- **Judge by necessity, not length.** Apply the same triage to a 3-minute clip as to a 3-hour talk — the criterion
  is whether watching it is genuinely worth the user's time, full stop. Never wave a video through as "too short
  to bother" or decline to triage it for being brief; 5 minutes saved, many times over, is exactly the point.
  Length informs only the time-saved estimate, never whether the skill runs or what the verdict is.
- **One video on demand, never a backlog grind.** Bulk-digesting a watch-later list feeds the very compulsion the
  user is trying to escape; bulk-deleting it is healthier. See Workflow step 0.
- **No captions → transcribe locally; never hallucinate.** If a video has no captions, fall back to local Whisper
  transcription (see Environment + Workflow step 1). Only stop with "no transcript available" when even the audio
  can't be fetched (private / age-gated / region-blocked). Never fabricate a summary from the title/thumbnail.
- **Check currency, not just truth.** Videos go stale; flag superseded/outdated claims as loudly as false ones,
  and record both the original and the corrected fact in 求證結果.
- **Watching is not endorsement.** When a claim fails fact-checking, say so plainly in both the note and report.
- The sub-agent reads and reasons; it never writes vault files. The main agent does all filing.
- Plain, terse vault writing — no emoji, plain Markdown — matching existing `Personal/Reference/` notes.
- You file; you do not delete or rewrite the user's existing notes.
