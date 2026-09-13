---
name: fandom-news
description: The morning digest of everything the user follows, and sports small-talk answered from today's headlines. Use when the digest cron fires, or the user asks what happened with their teams.
---

# Fandom News — the morning read

The user never hears the word "digest": in their language it is the
**resumo da manhã** (pt-BR) or **morning roundup** (EN). The command keeps
its name; the words they read do not.

One command, one message:

    /opt/hermes/.venv/bin/python3 /var/lib/hermes/skills/fandom-watch/scripts/fandom.py digest

The final response of your turn IS the digest — the cron's `--deliver`
relays it to the owner's chat. Compose it in their language, scannable in
one glance, using the reply formats of `fandom-watch/SKILL.md` — and calling it the
resumo da manhã / morning roundup, never "digest".

## Shape

Header with the date, then per followed subject — most news first:

- ⚽/🏀/🏈/🎮 **name** — N notícias
- One line per headline, link included, 🛒 *Mercado:* prefix for `transfers`
- ⚠️ degraded sources last, with the promise to retry

`"quiet": true` is the two-line version. Never invent, never restate a
headline the JSON did not carry.

## Sports small-talk

"e o jogo do Mengão ontem?" is a `fandom.py matchday <key>` question first —
state the result only if the JSON carries a `score` — and a `news` question
second. When both come back empty, the honest answer is "não achei" plus
the offer to follow more feeds, never a guess from memory.
