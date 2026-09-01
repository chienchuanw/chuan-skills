# Concert lighting design language

The craft reference behind this skill. It exists so the design work is grounded
in how concert lighting actually reads to an audience, rather than in whatever
sounds impressive. Consult it when writing the show bible and when designing
each song; cite it when explaining a choice to the user.

None of this is law. It is the set of defaults a working designer departs from
*on purpose* — which is the only way a departure means anything.

---

## 1. What each position says

Fixtures are not interchangeable brightness. Each position makes a different
statement, and a look is built by choosing which statements to make.

| Position | What it does | Watch out for |
|---|---|---|
| **Back light** | Separates the artist from the background, draws the silhouette, and makes beams visible in haze. The primary source of *scale* in concert lighting. | Alone it renders a silhouette — the face disappears. That is a choice, not an accident; make it knowingly. |
| **Front light** | Makes the face readable. Mandatory whenever the audience or camera must see expression. | The fastest way to flatten a show. Full front light erases depth, colour and drama. Use the minimum that reads. |
| **Side light** | Gives the body shape and three-dimensionality. Low sides are inherently dramatic. | Can be unflattering straight into the eyes at head height. |
| **Top light** | Isolates. A tight top pool is the loneliest image in the rig. | Deep shadows in the eye sockets; usually needs a touch of front to stay human. |
| **Beam / aerial** | Designs the *air*, not the performer. Delivers scale, spectacle and rhythm. | Invisible without haze. A beam look with no atmosphere is wasted rig. |
| **Audience / house** | Turns a performance into an event — the crowd becomes part of the picture. | Blinding the front rows; and it kills any darkness on stage, so it is a spend, not a freebie. |

**The practical consequence:** "make it bigger" almost never means "raise the
dimmer". It means add a position that is not currently speaking.

---

## 2. Contrast is the only currency

A look reads as big only relative to what preceded it. This single principle
outranks everything else in this file.

- **Spend from a budget.** If the rig is at full by the third song, songs four
  through twenty-two have nowhere left to go. Plan the show's ceiling and
  approach it late.
- **Repetition dulls.** Two consecutive full-white hits: the second one lands at
  perhaps half the impact of the first. If the user asks for back-to-back peaks,
  say so once, offer to strip one of them back so the other detonates, and then
  do whatever they decide.
- **Darkness is a design element.** The most powerful chorus hit is preceded by
  the emptiest bar in the song. Negative space is not the absence of design; it
  is the setup.
- **Stillness makes movement mean something.** A rig that never stops moving is
  a rig with no accents.

---

## 3. Section conventions

Starting points for the section names that show up in a typical cue CSV. Read
them together with the measured energy from `song_energy.py` — and when the
measurement disagrees with the convention, the disagreement is the interesting
part of the song. Design that, don't flatten it.

| Section | Default intent |
|---|---|
| **PGM IN / pre-show** | Holding state. Minimal, no focus on stage. |
| **INTRO** | Establish the song's palette and its world. Often back light only — a silhouette that says "something is starting" without showing everything. |
| **VER (verse)** | Restraint. Keep tools in reserve. Enough front light for the face if there is IMAG or an emotional lyric. |
| **PRE / RISE / BUILD** | The mechanism, not the payoff. Add one layer at a time, tighten beam angles, lift intensity, accelerate movement. The audience should feel it coming. |
| **CHOR (chorus)** | Release. Either the full statement — more positions, saturation, movement, audience light — or, once per show, the opposite: a sudden strip to a single source, which hits harder than a wash ever could. |
| **FILL / TURNAROUND** | Breathe. Come back down so the next chorus has somewhere to arrive from. |
| **BRIDGE / SOLO** | Change the rules. New colour family, new position, isolate whoever is playing. This is where a show earns its variety. |
| **END** | Resolve. Collapse to one source, or hold a full wash and take it out clean. Decide which, and make the fade time carry the meaning. |

---

## 4. Colour

- **Two to three colour families per song**, plus open white as an *event*. More
  than that and the song has no identity.
- **Saturation reads as mood; open white reads as reality.** Going to white is
  the strongest colour move available — which is exactly why it should be rare.
- **Complementary depth:** a warm key against a cool back light (or the reverse)
  separates the performer from the stage far better than any intensity change.
- **Skin matters.** Green and deep blue on faces read as illness. If the face
  must be seen, the front source stays close to white or a gentle tint.
- **Colour identity per artist** carries across a multi-artist show: the audience
  learns, without being told, when a new act has begun. The `setlist` skill
  already colours the master cue list by artist — keep the palettes consistent
  with that.

---

## 5. Movement

- Movement serves the beat or the emotion. Movement that only fills time reads as
  nervousness.
- **Symmetric / mirrored** movement reads formal, anthemic, monumental.
  **Asymmetric** reads chaotic and energetic. Pick deliberately; a rig doing both
  at once reads as broken.
- A slow position drift through a held section reads as *growth*. The same drift
  at speed reads as *agitation*.
- Stopping movement dead on a downbeat is one of the sharpest accents available,
  and costs nothing.

---

## 6. Time is half the design

The same look at different times is a different emotion.

| Fade | Reads as |
|---|---|
| `0` | Impact. A hit. |
| `0.3 – 0.8` | A snap that still has body — punchy without being brittle. |
| `2 – 5` | A swell. The audience notices the change happening. |
| `6+` | Drift. The audience notices only that the picture is now different. |

**Layered time** is where a design stops looking amateur. Giving positions
different delays turns a flat change into a directional one:

- back → sides → front reads as something **approaching** the audience;
- front → sides → back reads as something **receding**.

Delays of 0.1–0.4 s between layers are enough. The audience will not consciously
see the stagger; they will feel that the picture has depth.

**The classic hit:** fade in at `0`, fade out slow. Instant arrival, reluctant
departure.

---

## 7. Signature looks

A show needs three to five looks that recur across the night, each recognisable
and each with a job (for example: an intimate isolation, a full anthemic
statement, an aerial spectacle). They give the show an identity and let the
audience learn its visual language, so a callback in the encore actually lands.

Every song should say which signature look it draws on and how it varies it. If
a song's design cannot be traced back to the show bible, either the song is
genuinely a deliberate outlier, or the design has drifted — and drift across
twenty-two songs is how a show ends up looking like a pile of unrelated ideas.

---

## 8. Anti-patterns

Each of these is common, and each is worth pushing back on once.

- **Everything at full, all night.** No budget left, no contrast, no peaks.
- **Front light permanently on.** Kills depth in every single look.
- **Perpetual motion.** With no stillness, nothing can be an accent.
- **Colour changing every cue.** Nothing for the eye to hold.
- **Designing the chorus first.** Then the bridge and the final chorus have
  nowhere left to go. Design the *arc*, then the moments.
- **Beams without haze.** Expensive fixtures rendered invisible.
- **Losing the face at the emotional peak.** If the audience cannot see the
  singer when the lyric matters most, the look is wrong however beautiful it is.
- **Symmetry by default.** A perfectly mirrored rig doing perfectly mirrored
  things all night becomes wallpaper.

---

## 9. Follow spot

The spot operator is a person reading a sheet in the dark, so the sheet must be
unambiguous and must give lead time.

For every follow-spot cue specify: **which cue** it belongs to, **who** to pick
up, **body size** (head / half / full / wide), **colour frame**, **intensity**,
and **how** it arrives and leaves (snap, or a fade with a time).

Two rules that matter more than the rest:

- **Call the pickup before the moment.** An operator needs warning to find a
  performer in the dark; a cue that says "pick up the singer" at the instant the
  singer must be lit is a cue that will be late.
- **Say when to drop.** Unspecified outs are how a spot ends up sitting on an
  empty piece of stage for an entire verse.
