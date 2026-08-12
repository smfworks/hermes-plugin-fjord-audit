---
name: hermes-fjord-audit
description: "Use when auditing Hermes health/sprawl. Structural scan + honest gap scoring."
version: 1.0.0
author: SMF Works / Team Fjord
license: MIT
metadata:
  hermes:
    tags: [hermes, audit, health, skills, multi-agent, fjord]
    related_skills: [hermes-agent, agent-watchdog]
---

# Hermes Fjord Audit

## Overview

Look **inward** before a multi-agent sprint. A fjord is a drowned glacial valley — the bedrock shows. This skill pairs the `fjord-audit` plugin tools with a human assessment protocol for Hermes as platform and as a multi-profile team.

## When to Use

- Start of a crew challenge or long autonomous run
- "Why is this profile heavy / slow / forgetful?"
- Quarterly honest platform retros
- Before blaming the model for ops failures

Don't use for: live network connectivity alone (`hermes doctor`), or writing new skills without first checking sprawl.

## Procedure

1. **Filesystem scan** — call `fjord_scan` (or `hermes fjord scan`). Record skill count, oversized skills, memory chars, plugin dirs, profile list.
2. **Score** — call `fjord_score`. Capture grade, friction IDs, recommendations.
3. **Live doctor** — run `hermes doctor` and `hermes status`. Connectivity and npm advisories are out of band for the plugin.
4. **Team layer** — note bridge status (`smf-bridge status`), which profiles have gateways, and whether coordination is `live|delegated|hybrid`.
5. **Compare peers honestly** — Claude Code / Codex / OpenClaw class tools: Hermes wins on multi-platform gateway, skills self-improvement, provider-agnostic routing, profiles. Gaps often: skill-index tax, bridge fragility, plugin enablement friction, multi-agent idle/rework without a cell protocol.
6. **Write the assessment** — strengths, gaps, friction, underused strengths, one-sprint fixes vs structural fixes.
7. **Act** — curator archive, memory compress, enable needed plugins, freeze interfaces before parallel work.

## Completion criteria

- [ ] Numeric scan + grade on disk
- [ ] Doctor output summarized (not ignored)
- [ ] Bridge mode disclosed
- [ ] At least three concrete gaps with owners
- [ ] At least one underused strength named

## Common Pitfalls

1. Treating `hermes doctor` green as "no skill sprawl."
2. Faking offline agents as live in the roster.
3. Adding more skills to fix coordination (usually makes index worse).
4. Soft-memory full of task logs instead of durable preferences.

## Lofoten note

Stockfish is air-dried in cold wind — preservation by exposure. Fjord audit is the same move: hang the state in open air and see what hardens.
