# Security Policy

## Scope

`fjord-audit` is a **filesystem-only** inspector. It does not open network sockets, does not execute scanned skill code, and does not print `.env` values.

## Reporting

Email security concerns to the SMF Works maintainers via GitHub Security Advisories on this repository. Do not open a public issue for suspected secret leakage.

## Guarantees and non-guarantees

- Config snapshots record **model/provider keys only**, never API tokens.
- `hermes_home` is resolved with `Path.expanduser().resolve()`. Null bytes are rejected.
- Gateway state files larger than 64KB are not parsed.
- This plugin will happily scan any directory you point it at. Treat `hermes_home` as trusted operator input.

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes |
| 1.0.x   | Best-effort |
