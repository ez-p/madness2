# Madness

Django web application that generates a random NCAA March Madness bracket according to team seeds.  The chance of a team advancing in the tournament is proportional to that team's seed.  For more details, read the help system.

## Installation

This app runs on Python 3.12 and Django 5.2. Docker is the one supported way to
run it locally, so dependency versions stay consistent across machines.

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
  No local Python installation is required.

### One-time setup

Clone the repo, then from the project root:

```bash
docker compose build                                   # build the image
docker compose run --rm web python manage.py migrate   # create the database schema
docker compose run --rm web python manage.py import    # load teams/seeds for 2015-2017
```

You only need to redo `docker compose build` if `Dockerfile` or `requirements.txt`
change. `migrate`/`import` only need to be rerun if the database is reset (see below).

## Running

```bash
docker compose up            # start the app, logs to your terminal
docker compose up -d         # same, but detached (runs in the background)
```

Once it's up, visit **http://localhost:8000**.

```bash
docker compose logs -f web   # follow logs (useful if running detached)
docker compose stop          # stop the app, container/data kept for next `docker compose up`
docker compose down          # stop and remove the container (db data in the `dbdata` volume still survives)
```

### Making code changes

The project folder is mounted into the container, so edits to `.py` and template
files take effect immediately — Django's dev server auto-reloads on save, no
rebuild or restart needed. Only rebuild (`docker compose build`) after changing
`Dockerfile` or `requirements.txt`.

### Resetting the database

```bash
docker compose run --rm web python manage.py import   # wipes and reloads Year/Team/RegionData
```

To start completely fresh (including migrations):

```bash
docker compose down -v                                  # removes the db volume too
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py import
```

### Running one-off management commands

Anything from `manage.py`, e.g. the CLI simulator:

```bash
docker compose run --rm web python manage.py cli -m 2 -e SeedOdds
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py shell
```

### Running with gunicorn (prod-like)

The dev server (`manage.py runserver`) is what `docker compose up` uses by
default. To try it behind gunicorn instead:

```bash
docker compose run --rm --service-ports web gunicorn madness.wsgi --bind 0.0.0.0:8000 --log-file -
```

## Todo
* Create a user profile page
* Verify options are logical when creating using options
  * Don't let user manually select a team with a very low seed - takes forever
  * Verify mutually exclusive teams
* Add some javascript to avoid reloading pages
* Print tourney to a file
* Add caching

## License
See LICENSE.txt
