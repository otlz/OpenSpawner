# Versionierung

Dieses Projekt verwendet [Semantic Versioning](https://semver.org/lang/de/).

## Aktuelle Version

**Version**: 0.1.0 (Entwicklung)
**Release-Datum**: Januar 2026
**Status**: Alpha

## Versionierungsschema

```
MAJOR.MINOR.PATCH

MAJOR: Inkompatible API-Aenderungen
MINOR: Neue Features (rueckwaertskompatibel)
PATCH: Bugfixes (rueckwaertskompatibel)
```

### Pre-Release Versionen

- `0.x.x` - Entwicklungsphase, API kann sich aendern
- `1.0.0` - Erstes stabiles Release

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md) fuer detaillierte Aenderungen.

## Upgrade-Pfade

### Von 0.0.x auf 0.1.0

Keine Breaking Changes. Einfaches Update moeglich:

```bash
bash install.sh
```

## Git-Tags

Releases werden mit Git-Tags markiert:

```bash
# Alle Tags anzeigen
git tag -l

# Zu spezifischer Version wechseln
git checkout v0.1.0
```

## Geplante Features

### Version 0.2.0 (geplant)

- [ ] Container Auto-Shutdown nach Inaktivitaet
- [ ] Volume-Persistenz fuer User-Daten
- [ ] Admin-Dashboard

### Version 1.0.0 (geplant)

- [ ] Multi-Template-Support
- [ ] API-Rate-Limiting
- [ ] PostgreSQL-Support (Standard)

---

Zurueck zur [Dokumentations-Uebersicht](../README.md)
