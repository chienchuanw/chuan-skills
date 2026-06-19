# Cue options beyond the empty-placeholder default

The default this skill builds is the right one for almost every music show: an
**empty cue per section, triggered by Go, labelled by name**, with the timecode
kept only as reference. The operator walks the song by hand and programs the
looks into these shells later. This file documents the deliberate opt-ins for
when a song genuinely wants more — apply them only when the user asks.

## Writing the time onto the cues

`--note-col time` adds, after each Store, a line like:

```
Assign Cue <n> Sequence <seq> /note="@8.2s"
```

The Note is a free-text field shown in the cue sheet — handy as a section
time-marker for the operator. It does **not** affect triggering. (Note text is
not readable back over this console's Telnet, so verify on the desk.)

## Auto-advancing cues (Trig: Follow / Time / Timecode)

By default every cue is `Trig = Go` (manual). To make cues advance themselves,
set the trig type and time per cue:

```
Assign Cue <n> Sequence <seq> /trig=follow              # fire when prev cue's fade ends
Assign Cue <n> Sequence <seq> /trig=time /trigtime=2.0  # fire 2.0s after prev cue started
```

- **Follow** chains cues back-to-back (good for a fast multi-part hit).
- **Time** waits a fixed delay — you could derive `trigtime` from the gaps
  between the CSV's `time` values (Δ between consecutive rows).
- **Timecode** (`/trig=timecode`) binds a cue to an SMPTE/MIDI timecode and
  needs a timecode show running on the console — only meaningful when the show
  is timecode-driven. Don't reach for this unless the user runs timecode.

Reserve auto-advance for songs the user explicitly wants automated; the
name-driven setlist engine is otherwise a manual operating model and silently
automating cues would surprise the operator.

## Cue fades

The CSV's `fadeIn`/`fadeOut` columns (often all 0) can be pushed onto cues:

```
Assign Cue <n> Sequence <seq> /fade=<seconds>
```

Empty placeholder cues carry no values, so a fade time has nothing to fade until
the operator programs content. Set fades when (or after) the looks are
programmed, not at skeleton-build time, unless the user wants the timing
pre-seeded.
