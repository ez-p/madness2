from django.core.management.base import BaseCommand
from django.conf import settings

import sys
import time

import tournament.engine.data as data
from tournament.engine.tourney import *
from tournament.engine.region import *
from tournament.management.commands._printer import Printer
from tournament.management.commands import _stats as stats

def find_region(year, name):
    all_regions_cache = data.all_regions(year)
    for region in all_regions_cache:
        names = []
        for entry in all_regions_cache[region].values():
            names.append(entry['name'])
        if name in names:
            return region

def possible_matchup(year, winner, second):
    w_region = find_region(year, winner)
    s_region = find_region(year, second)

    if w_region == s_region:
        d = "({})".format(w_region.capitalize())
        print("Selected teams are in the same region {}".format(d))
        return False

    if data.exclusives(year)[w_region] == s_region:
        d = "({}, {})".format(w_region.capitalize(), s_region.capitalize())
        print("Selected team regions are mutually exclusive {}".format(d))
        return False

    return True

def verify_team_name(year, name):
    if not name:
        return True

    for r in data.all_regions(year).values():
        for team in r.values():
            if name == team['name']:
                return True
    return False

def check_input(year, madness, winner, second):
    if not verify_team_name(year, winner):
        print("Team name invalid: '{}'".format(winner))
        return False

    if second:
        if not verify_team_name(year, second):
            print("Team name invalid: '{}'".format(second))
            return False

    if second and winner:
        if not possible_matchup(year, winner, second):
            return False
    return True

class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named arguments
        parser.add_argument('-m', '--madness', type=int, default=1, help="Specify madness level")
        parser.add_argument('-w', '--winner', help="Specify the winner")
        parser.add_argument('-s', '--second', help="Specify the runner-up")
        parser.add_argument('-f', '--file', help="Save tournament results to a file", action='store_true')
        parser.add_argument('-e', '--engine', choices=['SeedOdds','FiftyFifty'], default='SeedOdds',
                help="Specify the engine used to run the tournament.")
        parser.add_argument('-x', '--stats', type=int, default=0, help="Do a statistics run")
        parser.add_argument('-y', '--year', type=int, default=settings.DEFAULT_YEAR, help="Specify year")
        parser.add_argument('-d', '--db', help="Save tournament results to database", action='store_true')

    # Get'r done
    def handle(self, *args, **options):
        madness = options['madness']
        winner = options['winner']
        second = options['second']
        iterations = options['stats']
        year = options['year']
        
        if options['engine']  == "SeedOdds":
            from tournament.engine.algorithms.seedodds import SeedOddsMatchup as engine
        elif options['engine']  == "FiftyFifty":
            from tournament.engine.algorithms.fiftyfifty import FiftyFifty as engine
        else:
            # Shouldn't ever get here...
            print("Invalid Engine!")
            parser.print_usage()
       
        if not check_input(year, madness, winner, second):
            sys.exit()

        if iterations:
            s = stats.Stats(year, winner, second, madness, engine, iterations)
            s.run()
            sys.exit(0)

        tourney = Tournament(year, winner, second, madness, engine)
        start = time.time()
        results = tourney()
        print("Execution time: {}".format(time.time() - start))

        printer = Printer(tourney, options['file'])
        printer.print_to_file(year)
        printer.print_to_screen()
        stats.print_stats(results)

        if options['db']:
            # Save the results to the database
            import tournament.views as views
            id = views._save_tournament(results)
            print("\nResults saved to database: {}".format(id))
