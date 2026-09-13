---
name: fandom-watch
description: Follow teams, leagues and esports scenes; fetch and filter the news; check matchday fixtures. Use when the user mentions a team or league to follow, asks what is new about their teams, asks about games, or when the news/matchday crons fire.
---

# Fandom Watch — the engine

Every followed subject, every headline, every fixture goes through one CLI.
The scripts are mechanical and answer **one JSON object on stdout**; you own
every human word around them.

    FANDOM=/var/lib/hermes/skills/fandom-watch/scripts
    /opt/hermes/.venv/bin/python3 $FANDOM/fandom.py <command>

Exit 0 is success, 2 is failure with an `error` field — read it, never guess.

## Following — the first-value rule

A message naming a team, league or scene is always a follow request:

    fandom.py teams add Flamengo --sport futebol --aliases "Mengão" "Fla"

Aliases are what match headlines — include nicknames ("Timão", "Mengão",
"Verdão") and common spellings. For esports, the scene is the subject:

    fandom.py teams add CBLOL --sport esports --aliases "CBLOL" "LoL brasileiro"

To attach fixtures (best-effort), find the provider id first and re-add:

    fandom.py search_team Corinthians     # -> results[].id
    fandom.py teams add Corinthians --sport futebol --source-id 134284

Confirm the follow in one short line. Never gate it on onboarding.

## The news sweep

    fandom.py news --limit 5

Run it when the user asks what's new, or when the digest cron fires. The
output groups headlines by followed team. Present them in the user's
language — **only headlines the JSON carries**, each with its link. A
headline the script did not output does not exist.

## Matchday — honest by design

    fandom.py matchday            # every followed team
    fandom.py matchday <key>      # one team

A team without `source_id` answers with a `note` — say the fixture is not
confirmed instead of guessing. A `result` with a `score` is the only placar
you may state. The free provider often answers empty: that is "não achei
jogo confirmado", never "não tem jogo".

## Reply formats

Follow confirmed:

    ✅ Seguindo *Flamengo* 🇧🇷 ⚽ — notícias do ge, ESPN e BBC, digest todo dia às 08:30.

Morning digest (the final response IS the digest — cron `--deliver` relays it):

    📰 *Fandom do dia* — 13/09

    ⚽ *Brasileirão* — 4 notícias
    • Flamengo vence e assume a liderança — ge.globo.com/…
    • 🛒 *Mercado:* Vasco propõe por atacante do Bahia — ge.globo.com/…

    🏀 *NBA* — 1 notícia
    • Lakers anunciam renovação — espn.com/…

    ⚠️ Sem resposta de: espn.com — tento de novo amanhã.

Movement marks: 🛒 `transfers` are market *rumor*, labeled as such. Sport
emojis: ⚽ futebol, 🏀 basquete, 🏈 NFL, 🎮 e-sports. Flag follows the league
country (Brasileirão 🇧🇷, NBA 🇺🇸, CBLOL 🇧🇷). A quiet day is two lines, not
silence:

    📰 *Fandom do dia* — nada se mexeu nas 3 cenas que você segue. Dia de treino.

## Config

    fandom.py config get
    fandom.py config set timezone=America/Sao_Paulo digest_time=08:30 language=pt-BR

`teams list` and `config set` answer `onboarding_missing` — any key there
means the `fandom-onboarding` conversation is unfinished; start it (after the
first follow, never before).
