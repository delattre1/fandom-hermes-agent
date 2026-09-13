---
name: fandom-onboarding
description: First-contact setup — timezone, language, digest time and which teams to follow. Use when a follow exists but onboarding is unfinished (onboarding_missing is non-empty), or the user asks to change these preferences.
---

# Fandom Onboarding — once, after the first value

The first-value rule outranks this conversation: **a team or league is
followed before any question is asked.** Onboarding starts only after a
follow is confirmed, and it is a conversation — one or two questions per
message, in the user's language.

Finished means `fandom.py teams list` answers `onboarding_missing: []`.

## The questions, in order

1. **Language** — detected from their messages; save the first time they
   reply (`config set language=pt-BR`).
2. **Timezone** — needed so the digest lands at the right local hour. A city
   name becomes its IANA zone. Save it.
3. **Digest time** — offer the default: "resumo todo dia às 08:30, bom?"
   Save as `digest_time=HH:MM`, `digest_enabled=false` if they decline.
4. **What else to follow** — the BR seed (Brasileirão, CBLOL, NBA) is already
   in; ask what they actually root for, one at a time, and add each with its
   aliases. `teams remove <key>` for what they do not want.

## Timezone is fixed at boot

The container's `TZ` is set from `timezone` in the config **when the
container starts**. After saving a timezone, compare with `echo $TZ`:

- Same: register the schedules now (below).
- Different: say the zone lands "no próximo reinício" and register only after
  that restart. **Never register schedules whose zone disagrees with the
  container** — they would fire at the wrong local hour, silently.

## Registering the schedules (after config is complete)

Registered once, by you, from a turn (a turn carries the gateway's
environment; a bare exec does not):

    /opt/hermes/bin/hermes cron create "30 8 * * *" \
      "Run the fandom digest now: execute fandom.py digest and compose the morning digest in the user's language as your final response." \
      --name fandom-digest --skill fandom-news \
      --deliver "plow_chat:${PLOW_HOME_CHANNEL}"

    /opt/hermes/bin/hermes cron create "0 12,19 * * *" \
      "Run the fandom matchday now: execute fandom.py matchday, and only if a followed team has a game today or a fresh result, compose the matchday message in the user's language and post it with post_chat.py; otherwise post nothing and end with NO_REPLY." \
      --name fandom-matchday --skill fandom-watch

The digest's `30 8` follows the user's `digest_time` (re-register after a
change — remove the old job first with `hermes cron remove fandom-digest`).
If a job already exists, skip it — never duplicate a schedule.
