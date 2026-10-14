# Lebanese Arabizi (Franco) spelling convention — v1

Why this exists: the 2026-10 audit of `feedback/human_feedback.jsonl` found the 45 recorded
corrections pull in two incompatible directions. One reviewer corrects toward spoken Lebanese
(`shighl → sheghel`, `b ser3a → bser3a`, `sho b7ib? → shou bet7eb?`); another corrects toward
Modern Standard Arabic written in Latin letters (`ana mut3ab → ana mut3abaton`,
`alshar3 mazdaham → al touroukat mouzdahima`). Without one target, the same row is "correct" to
one reviewer and "wrong" to the next — and no automatic check can do better than the labels.

**The target is spoken Lebanese as people actually text it.** Not MSA, not a transliteration
scheme. If a Beiruti would not type it in WhatsApp, it is wrong — even when it is a faithful
rendering of the Arabic source.

`lff audit` enforces the mechanical rules; `normalize_franco()` fixes the mechanical ones.
Taste (word choice, naturalness) still needs a native reviewer — the rules only remove the
arguments that were never about taste.

---

## 1. Letters written as digits

| Digit | Arabic | Example |
|---|---|---|
| `2` | ء / ق (glottal stop) | `2ahwe` (قهوة), `ja2e3` (جائع), `bati2` (بطيء) |
| `3` | ع | `3andak` (عندك), `ma3ak` (معك) |
| `5` | خ (or write `kh`) | `5alas` / `khalas` |
| `7` | ح | `7abibi`, `mar7aba` |
| `8` | غ (or write `gh`) | `8ali` / `ghali` |

- **`kh` and `gh` are the default spellings**; `5` and `8` are accepted variants, not errors.
- A digit is only a letter when it replaces that sound. A digit must never carry an index,
  count or id (see §6).
- Lebanese ق is usually the glottal `2` (`2albe`, `2arib`). Write `q` only where the speaker
  really says it (`Qatar`, some religious or formal words).

## 2. No MSA endings or MSA vocabulary

Write the Lebanese word, not the Standard Arabic one.

| Write | Not |
|---|---|
| `ana mut3ab` | `ana mut3abaton` (MSA case ending) |
| `l tari2 ze7me` | `al touroukat mouzdahima` |
| `l share3 msakkar bi sabab l binaye` | `alshare3 mughlaq bisabab albina2` |
| `wen enta?` | `ayna anta?` |
| `shou bet7eb?` | `sho b7ib?` |

Dropped for good: `-oun`, `-aton`, `-un` case endings; `alsh-`/`almu-` MSA clusters glued to a
word; MSA verb forms where Lebanese uses its own (`mouzdahem` → `ze7me`).

## 3. The definite article

Write **`l`** as its own token: `l beit`, `l internet`, `l share3`.

- Not `al` (MSA), not glued (`alinternet`), not `el` (accepted in speech, but pick one in
  writing and `l` is the shorter).
- Before a sun letter, keep `l` in writing even when it assimilates in speech:
  `l share3`, not `sh share3`.

## 4. Prefixes attach, prepositions do not

| Attach to the word | Example |
|---|---|
| `b` (with/in) | `bser3a`, `bl beit` |
| `m` / `mn` (from) | `mnl beit` |
| `3a` (on/to) when a single unit | `3assa3a` is also fine as `3a l sa3a` |
| verb prefixes `b`, `m`, `ra7` | `b7eb`, `mroo7`, `ra7 rou7` |

Stand-alone words keep their space: `fi`, `ma3`, `3an`, `la`, `mesh`.

Negation is **`mesh`** (`mesh tamam`), not `ma7`, not `mich`.

## 5. Vowels and doubles

- Spell the vowel you hear: `sheghel` (not `shighl`), `jem3a` (not `jam3a`),
  `shou` (not `sho`), `nel3ab` (not `nlabab`).
- Double a consonant only when it is pronounced long: `bassita`, `motassel`, `yalla`.
  Never double by accident: `kkifak` → `kifak`.
- `sh` for ش (never `ch`), `j` for ج, `w` for و as a consonant.

## 6. Mechanical rules (enforced, never a judgement call)

1. **No counters or ids in the text.** `#1`, `(3254)`, `[8805]` are generator debris. 389,795
   of 392,183 generated rows carried one in October 2026.
2. **No Arabic script in a Franco field**, and no Franco in an Arabic field.
3. **Input and output must differ** (except `variants`/`summarize`, where identity is the point).
4. **One space between tokens**, no leading or trailing space, no double spaces.
5. **Lowercase**, except proper nouns (`Beirut`, `Jounieh`, `IDM`).
6. **Keep the source's punctuation**: a question in Arabic ends `?` in Franco too.
7. **No emoji or decoration** in dataset rows.

## 7. Worked examples

| Arabic | Write | Not |
|---|---|---|
| كيفك؟ | `kifak?` (m) / `kifik?` (f) | `keefak`, `kifak? #1` |
| شغل | `sheghel` | `shighl` |
| بسرعة | `bser3a` | `b ser3a` |
| أنا متعب | `ana mut3ab` | `ana muta3eb`, `ana mut3abaton` |
| ما عندك وقت؟ | `ma 3andak wa2et?` | `ma 7adak wakt?` |
| الإنترنت بطيء | `l internet bati2` | `al internet bat7i` |
| أنا مش فاهم | `ana mesh fahem` | `ana ma3a7am`, `ana mich fehem` |
| شو بتحب؟ | `shou bet7eb?` | `sho b7ib?` |

## 8. What this means for the existing data

- The 45 recorded corrections need re-reading against this convention. The MSA-leaning ones
  (about 30, all from the `anonymous` reviewer) are wrong under §2 and should not be treated as
  gold.
- `ai_first_pass` approved 104 of 105 rows it saw; those approvals carry no weight and the rows
  should be re-checked.
- Rows that only break §6 are fixed by `normalize_franco()` and never need a reviewer.
