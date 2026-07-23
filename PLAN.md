# Modernization Plan: Python 2 / Django 1.9 → Python 3.12 / Django 5.2 LTS

## Goal

Port madness2 from Python 2.7 / Django 1.9.5 to Python 3.12 / Django 5.2 LTS,
running on SQLite3 only (no Postgres/Heroku), with no functional or visual
regressions to the app as it exists today.

## Scope decisions (confirmed)

- **Django target:** 5.2 LTS (supported into 2028)
- **Python target:** 3.12
- **Database:** SQLite3 only. Drop `dj-database-url` and `psycopg2`, drop the
  `Procfile` and Heroku/`DATABASE_URL` handling. This becomes a Docker/local
  app, not a Heroku deployment.
- **Bug cleanup:** Fix pre-existing bugs opportunistically in files that are
  being rewritten anyway (see "Incidental bugs" below), rather than as a
  separate pass.
- **Admin theme:** `django-admin-bootstrapped` is dead (last released 2015,
  declares support only for Django 1.8) — drop it and use the stock Django
  admin.
- **Bootstrap/CSS:** `django-bootstrap3` is not actually used anywhere in the
  templates (Bootstrap 3 CSS/JS is pulled from a CDN directly in
  `base.html`) — drop this dependency entirely rather than upgrading it.
  Bootstrap 3 itself is EOL upstream, but re-theming to Bootstrap 5 is a
  separate, purely cosmetic project — out of scope here unless you want to
  fold it in.
- **Forms styling:** `django-crispy-forms` 2.x split Bootstrap template packs
  out of the core package. Since we're keeping the Bootstrap 3 look, add the
  `crispy-bootstrap3` package (maintained, third-party pack) alongside a
  current `django-crispy-forms`.
- **`on_delete` choice:** `CASCADE` on every `ForeignKey`, including the
  nullable ones (`Options.winner`/`second`, `RegionData.ff_match`/
  `exclusive`, `Round.region`, `Matchup.round`/`tournament`) — this matches
  Django <2.0's hard-coded delete behavior exactly. `null=True` on those
  fields only ever meant "optional at creation," not "survives deletion of
  the referenced row," so `CASCADE` is the no-behavior-change choice.
- **Dead password-hash code:** delete `RegisterView.form_valid`'s unused
  `hashlib.md5(password).hexdigest()` computation (Phase 1) rather than
  porting it to Python 3 bytes — the hash is never stored or read anywhere,
  so this is a pure simplification.
- **Cosmetic pre-existing bugs:** fix them while the files are open for other
  migration reasons — `base.html`'s malformed attributes
  (`navbar=default`/`container=fluid`/`navbar=header` → hyphens) alongside
  the logout-button change it already needs, and `print_bracket`'s
  nonexistent `'ok'` template while `tournament/views.py` is being edited.
- **`SECRET_KEY`:** leave hardcoded in `settings.py`. Out of scope for this
  migration; revisit as a separate security task later.
- **README:** stays Docker-only. One documented path to maintain; Docker
  also keeps dependency versions consistent across machines.

## Target dependency versions

| Package | Current | New | Notes |
|---|---|---|---|
| Python | 2.7 | 3.12 | |
| Django | 1.9.5 | 5.2.x (LTS) | |
| django-extensions | 1.6.7 | 4.1 | actively maintained, supports 5.2 |
| django-crispy-forms | 1.6.0 | 2.6 | Bootstrap pack now separate |
| crispy-bootstrap3 | — (new) | latest | replaces built-in bootstrap3 pack |
| whitenoise | 2.0.6 | 6.12.x | storage backend setting changes (see below) |
| gunicorn | 19.6.0 | latest 2x | keep for `docker compose` prod-like runs; drop `Procfile`/Heroku-specific bits |
| dj-database-url | 0.4.1 | — (removed) | no longer needed, sqlite3 only |
| psycopg2 | 2.8.6 | — (removed) | no Postgres |
| six | 1.10.0 | — (removed) | was a Py2/3 compat shim, unneeded |
| wheel | 0.26.0 | — (removed, or let pip manage it) | not a runtime dependency |
| django-admin-bootstrapped | 2.5.7 | — (removed) | dead package, use stock admin |
| django-bootstrap3 | 7.0.1 | — (removed) | unused in templates |

I'll pin exact versions in `requirements.txt` once we start implementing
(latest patch release of each at that time), rather than baking specific
patch numbers into this plan.

## Phased approach

Each phase should leave the app in a working, testable state. Recommend
committing after each phase.

### Phase 0 — Safety net before touching anything

- Add a minimal automated regression suite (`tournament/tests.py`, currently
  empty) covering, at minimum:
  - Running a full tournament simulation via `SeedOddsMatchup` and
    `FiftyFifty` and asserting a champion is produced without error.
  - The `import` management command populating `Year`/`Team`/`RegionData`.
  - Core views: home page, generate tournament, view result, options form
    (including the "same region" / "mutually exclusive region" validation
    errors), register/login/logout.
- This is what will actually tell us whether behavior changed at each phase.
- **Use the existing running container (`madness-web-1`, Python 2.7.18 /
  Django 1.9.5, published at `http://localhost:8000/`) as the live
  pre-migration baseline** rather than spinning up a separate throwaway
  Python 2 container for this:
  - Walk the golden path against it now (register → login → generate
    tournament → view result → options form, including the "same region" /
    "mutually exclusive region" validation errors → logout) and capture the
    real responses/HTML as the baseline to diff against later.
  - Run the fixed-input bracket generation baseline directly inside it —
    `docker exec madness-web-1 python manage.py cli -m 1 -e SeedOdds` (and
    `-e FiftyFifty`) — and save the output as a manual comparison point,
    since the RNG-based simulation isn't fully deterministic bracket-to-bracket.
  - **Keep this container running through Phase 4** so the new Django 5.2
    app can be diffed against it live, page-by-page, instead of relying on
    a static snapshot or memory of "what it looked like before."
  - **Port/volume conflict:** this container already holds port 8000 and
    its own SQLite volume. The new Django 5.2 dev/Docker setup must run on
    a different published port (e.g. 8001) for the two to coexist, and we
    need to decide up front whether the new stack points at a copy of the
    existing SQLite file (safer — no risk of the old app mutating data
    mid-comparison) or a fresh one seeded via `manage.py import` (per
    Phase 4's own verification step). Recommend a copy, so the baseline
    data is frozen and identical on both sides for the diffing in Phase 4.

### Phase 1 — Python 2 → 3 syntax fixes (no Django version change yet)

Do this first, independent of the Django upgrade, so the two migrations
don't get tangled together. At this point we're still on Django 1.9 but
running under Python 3 is not actually possible with Django 1.9 (it doesn't
support Py3 in that combination cleanly) — in practice Phases 1 and 2 will
need to land together before the app runs at all. List here for tracking,
implement together with Phase 2:

- `tournament/engine/round.py`: `xrange` → `range`.
- `tournament/management/commands/cli.py`, `tournament/engine/region.py`,
  `tournament/management/commands/_stats.py`: convert all bare `print "..."`
  statements to `print(...)`.
- Implicit relative imports (Python 2 only, `ImportError` under Python 3):
  - `tournament/engine/tourney.py`: `import region`, `import data` →
    `from tournament.engine import region, data`
  - `tournament/engine/region.py`: `import team`, `import round` →
    `from tournament.engine import team, round` (note: `round` shadows the
    builtin — rename the module-level alias where it's used as a loop
    variable to avoid confusion, but the import itself is fine since it's
    namespaced)
  - `tournament/engine/algorithms/fiftyfifty.py`,
    `.../seedodds.py`: `from matchup import Matchup` →
    `from tournament.engine.algorithms.matchup import Matchup`
  - `tournament/management/commands/cli.py`: `from _printer import Printer`,
    `import _stats as stats` → `from tournament.management.commands._printer
    import Printer`, `from tournament.management.commands import _stats as
    stats`
  - `tournament/management/commands/import.py`: `import _data_2015 as
    data2015` (and 2016/2017) → same pattern, full module path
- `tournament/management/commands/import.py`: `.iteritems()` →
  `.items()`
- `tournament/models.py`: `__unicode__` methods on `RegionData`, `Algorithm`,
  `Tournament`, `Region` are dead code under Python 3 (never called) —
  delete them, or merge their logic into `__str__` where a model doesn't
  already have one (`RegionData`, `Algorithm`, `Tournament`, `Region` don't
  currently have `__str__`, so their `models.Model` default repr would show
  instead — port the `__unicode__` body to `__str__` in each case).
- `tournament/engine/algorithms/matchup.py`: `__metaclass__ = abc.ABCMeta`
  (Python 2 syntax, silently does nothing under Python 3) → `class
  Matchup(metaclass=abc.ABCMeta):`
- `tournament/views.py` `RegisterView.form_valid`: delete the unused
  `hashlib.md5(password).hexdigest()` computation entirely (per the scope
  decision above) rather than porting it to Python 3 bytes — it's dead code,
  since `User.objects.get_or_create` never stores the hash on `User` and
  `authenticate()` re-checks against Django's own password hasher
  independently.
- `tournament/management/commands/cli.py`: `main()`'s exception handler
  does `print str(err)` (Py2 syntax) and the function itself, along with
  `usage()`/`help()`, is dead code — nothing calls them; `manage.py cli`
  runs through Django's `Command.handle()` entry point, not `main()`. Delete
  only `main()`/`usage()`/`help()`. This also removes the latent bugs in
  that dead path (missing `import getopt`, typo `tournamen.engine...`
  instead of `tournament.engine...`).
  **Do not** delete `find_region()`/`possible_matchup()`/
  `verify_team_name()`/`check_input()` — these are *not* dead: `main()`
  called them, but so does `Command.handle()` (the live entry point), via
  `check_input()` → `verify_team_name()`/`possible_matchup()` →
  `find_region()`. Keep all four; just convert their `print` statements to
  `print(...)`. Also double check `Command.handle()`'s own
  `print "Invalid Engine!"` gets converted, not swept up in the `main()`
  deletion by mistake.
- Integer division: `tournament/management/commands/_stats.py`
  `average = upset_total/self.iterations` changes from Python 2 floor
  division to Python 3 true division automatically. This is arguably a
  latent bug fix (stats become more precise), but worth a quick check that
  nothing downstream assumed an int.

### Phase 2 — Django 1.9 → 5.2 upgrade

Django's own upgrade path is incremental (each major version's release
notes list deprecations); jumping straight from 1.9 to 5.2 means we apply
all of the following at once since we won't run the intermediate versions.

**`madness/settings.py`:**
- `MIDDLEWARE_CLASSES` → `MIDDLEWARE` (renamed in 1.10; old-style middleware
  classes were removed in 2.0 anyway — `SecurityMiddleware`,
  `SessionMiddleware` etc. are all already class-based here, so this is a
  rename, not a rewrite).
- Remove `django.contrib.auth.middleware.SessionAuthenticationMiddleware`
  (removed in Django 1.11; folded into `AuthenticationMiddleware`).
- Remove `django_admin_bootstrapped` from `INSTALLED_APPS` per the scope
  decision above. (`django_bootstrap3` is *not* in `INSTALLED_APPS` today —
  only in `requirements.txt` — so its removal is a `requirements.txt`-only
  change, not a settings change.)
- Remove `dj_database_url` usage; `DATABASES['default']` becomes a static
  sqlite3 config only.
- Remove `USE_L10N = True` — this setting was removed entirely in Django
  5.0 (localized formatting is always on now); leaving it set is harmless
  under Django's tolerance for unknown settings but should be cleaned up
  while this file is open.
- Reconsider `SECURE_PROXY_SSL_HEADER` and `ALLOWED_HOSTS = ['*']` —
  both are Heroku-deployment leftovers in the same category as the
  `dj_database_url`/`DATABASE_URL` handling already being stripped for the
  Docker-only pivot. `SECURE_PROXY_SSL_HEADER` blindly trusts an
  `X-Forwarded-Proto` header that a local/Docker deployment has no reverse
  proxy setting, and `ALLOWED_HOSTS = ['*']` disables Django's host-header
  validation entirely. Narrow or remove both for the local/Docker context.
- `STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'`
  → Django 4.2+ prefers the `STORAGES` setting dict; whitenoise 6.x's
  equivalent is `whitenoise.storage.CompressedManifestStaticFilesStorage`
  under `STORAGES["staticfiles"]["BACKEND"]`.
- `CRISPY_TEMPLATE_PACK = 'bootstrap3'` → add `CRISPY_ALLOWED_TEMPLATE_PACKS
  = "bootstrap3"` per crispy-forms 2.x config (exact setting name to be
  confirmed against the crispy-bootstrap3 package's docs at implementation
  time).
- `SECRET_KEY` stays hardcoded (per the scope decision above) — untouched by
  this migration.
- Add `DEFAULT_AUTO_FIELD` setting (Django 3.2+ requires this to avoid
  migration warnings on every app; set to `django.db.models.AutoField` to
  match existing migration history, not `BigAutoField`, to avoid generating
  a spurious migration).

**`madness/urls.py`:**
- `from django.conf.urls import url` → `from django.urls import re_path` (or
  convert patterns to `path()` where they don't need regex — most of these
  are simple enough to become `path()` with converters, e.g.
  `<int:option_id>/`).
- `admin.site.urls` usage is already correct for modern Django.
- `auth_views.logout` (function-based view, removed entirely by Django 4.1)
  → `auth_views.LogoutView.as_view()`. Note `LogoutView` only responds to
  POST since Django 4.1 (GET-based logout was a security hardening change)
  — the logout link in `madness/templates/base.html` is currently an `<a
  href>` (GET). This needs to become a POST form (small button) instead of
  a link, or use a small JS-submitted form. Flagging as a real template
  change, not just a Python change.
- `from tournament.views import *` — works but is poor practice; consider
  explicit imports while this file is being edited anyway (optional
  cleanup, not required for the migration).
- Dead imports, unused anywhere in the file: `from django.views.static
  import serve`, `RedirectView`. Delete both while this file is open.

**`tournament/views.py`:**
- `from django.shortcuts import render_to_response` → remove; `render_to_response`
  was removed in Django 1.10. It's imported but never actually called
  anywhere in this file (dead import) — just delete the import.
- `from django.core.urlresolvers import reverse_lazy` → `from django.urls
  import reverse_lazy` (`django.core.urlresolvers` removed in Django 2.0).
- `request.user.is_authenticated()` (called as a method) →
  `request.user.is_authenticated` (property since Django 1.10; calling it
  as a function under 5.2 would evaluate a `CallableBool` truthily, but this
  shim was removed — must be updated).
- `print_bracket` view calls `render(request, 'ok')` — `'ok'` isn't a real
  template and this looks like a stub/placeholder that would 500 today too
  (pre-existing, not introduced by the migration). Fix while this file is
  open, per the scope decision above — return a minimal working response
  (or a real template) instead of the broken stub.
- Dead import, unused anywhere in the file: `from django.template import
  RequestContext`. Delete while this file is open.

**`tournament/models.py`:**
- `from __future__ import unicode_literals` — harmless no-op under Python 3,
  can be deleted for cleanliness across `models.py`, `apps.py`, and the
  migration files, though it isn't required to be removed.
- Every `ForeignKey` is missing `on_delete` (e.g. `RegionData.ff_match`,
  `RegionData.exclusive`, `RegionData.year`, `Team.year`, `Team.region`,
  `Options.year`, `Options.winner`, `Options.second`, `Options.algorithm`,
  `Tournament.year`, `Tournament.winner`, `Tournament.runnerup`,
  `Tournament.options`, `Region.tournament`, `Round.region`,
  `Matchup.team1`, `Matchup.team2`, `Matchup.winner`, `Matchup.round`,
  `Matchup.tournament`). `on_delete` became **required** in Django 2.0 — the
  app will not even import without this fixed. Use `on_delete=CASCADE`
  everywhere (per the scope decision above), including the nullable fields
  like `Options.winner`/`Options.second`, to preserve current behavior
  exactly.
- This will require a new migration (`makemigrations`) since `on_delete` is
  part of the field's migration state, even though it's not changing actual
  DB constraints for SQLite (SQLite doesn't enforce FK actions the same way;
  the app enforces cascade behavior at the Django ORM layer regardless of
  backend).

**`tournament/admin.py`:** No changes expected — plain
`admin.site.register(...)` calls remain compatible as-is.

**`tournament/forms.py`:** Uses `super(OptionsForm, self).__init__(...)` —
old-style `super()` calls still work fine in Python 3, no change required
(optional cleanup to bare `super().__init__(...)` while editing this file).

**Templates:**
- `madness/templates/base.html`:
  - `{% url 'django.contrib.auth.views.logout' %}` — this "URL name is a
    dotted view path" pattern was removed in Django 1.10; must become
    `{% url 'logout' %}`, paired with naming the new `LogoutView` route
    `'logout'` in `urls.py`.
  - Convert that same logout link from `<a href>` to a small `<form
    method="post">` + `{% csrf_token %}` + submit button, per the
    `LogoutView` POST-only change above.
  - Fix the pre-existing malformed HTML attributes while this file is open
    for the logout change (per the scope decision above): `navbar=default`,
    `container=fluid`, `navbar=header` → hyphens instead of `=`.
- No other templates reference removed template tags, `{% ifequal %}`, or
  other deprecated syntax — confirmed by grep across `tournament/templates`
  and `madness/templates`. `{% crispy form %}` usage in `login.html` /
  `register.html` continues to work with `crispy-bootstrap3` swapped in.

**Migrations:** The four existing migrations (`0001_initial` through
`0004_auto_20170308_1901`) are plain Python and should apply unmodified
under Django 5.2 — Django maintains migration-file backward compatibility.
After adding `on_delete` to every `ForeignKey` in `models.py`, run
`makemigrations` to generate a new migration capturing that field-state
change (schema-neutral on SQLite, but needed to keep migration state and
model definitions in sync).

### Phase 3 — Docker/tooling updates

- `Dockerfile`: `FROM python:2.7-slim` → `FROM python:3.12-slim`. Drop the
  Debian Buster archive-repo workarounds (`sed`/`apt.conf.d/99no-check-valid-until`),
  since a current Python 3.12 base image tracks a supported Debian release
  with live repos. Also drop `libpq-dev` from the `apt-get install` list —
  it's only needed to build `psycopg2`, which is being removed.
- `requirements.txt`: replace with the pinned versions from the table above.
- `docker-compose.yml`: `DATABASE_URL=sqlite:////app/data/db.sqlite3` env var
  can be removed since settings.py will hardcode sqlite3 — decide whether to
  keep the `dbdata` volume mount pointed at `/app/data` or move back to
  `BASE_DIR` default (`/app/db.sqlite3`) to match the simplified settings;
  recommend keeping the named volume for persistence but pointing
  `DATABASES['default']['NAME']` at that path directly in settings.py.
- `Procfile`: delete (Heroku-specific, out of scope per the decision above).
  If you want a "run with gunicorn" option preserved for local prod-like
  testing, that can move into `docker-compose.yml` or the README as an
  optional command instead.
- `README.md`: update the "Installation" section to drop the Python 2
  caveat. Stays Docker-only (per the scope decision above) — no native
  virtualenv workflow added.

### Phase 4 — Verification

- Run the Phase 0 test suite under the new stack.
- `python manage.py check` and `python manage.py makemigrations --check
  --dry-run` (should report no missing migrations once Phase 2's
  `on_delete` migration is committed).
- `python manage.py migrate` on a fresh sqlite3 file, then `python
  manage.py import` to confirm 2015/2016/2017 data loads.
- Manually walk the golden path in a browser per the repo's own testing
  norms: register → login → generate a default tournament → view result →
  save/remove bracket → create-with-options (including triggering the
  "same region" and "mutually exclusive" validation errors) →
  view-full-result → logout. With the Phase 0 baseline container
  (`madness-web-1`, still running at `http://localhost:8000/`) up
  alongside the new stack on its own port, diff each page/response
  live against the baseline rather than relying on memory or a static
  snapshot.
- Run `python manage.py cli -m 2 -e SeedOdds` and `-e FiftyFifty` and
  compare output shape against the Phase 0 baseline captured via `docker
  exec madness-web-1 python manage.py cli ...` (exact brackets will differ
  due to RNG, but structure/format should match).
- Once verification is complete and the new stack is confirmed
  behavior-equivalent, retire the baseline container (`docker compose down`
  / remove `madness-web-1`) and move the new stack onto port 8000.
- `python manage.py collectstatic` to confirm whitenoise's new storage
  backend setting works.
