import tournament.engine.region as region
import tournament.engine.tourney as tourney
import tournament.engine.data as data
import sys
import datetime

DEFAULT_ITER = 300000

def is_upset(match):
    seeds = [match.teams[0].seed, match.teams[1].seed]
    expected_winner = sorted(seeds)[0]
    if match.winner.seed != expected_winner:
        return 1
    return 0

def upsets(year, results):
    upsets = 0
    for r in data.all_regions(year):
        region = results[r]
        for round in region.rounds:
            for match in round.results:
                upsets += is_upset(match)
        upsets += is_upset(region.final)

    upsets += is_upset(results['semi1'])
    upsets += is_upset(results['semi2'])
    upsets += is_upset(results['championship'])
    return upsets

def print_stats(results):
    num_upsets = upsets(results['year'], results)
    sys.stdout.write("Number of Upsets: {} (Average: 18)\n".format(num_upsets))

class Stats:
    # 300,000 seems to be the limit without a crash on macbook pro
    def __init__(self, year, winner, second, madness, algorithm,
                 iterations=300000):
        self.year = year
        self.winner = winner
        self.second = second
        self.madness = madness
        self.algorithm = algorithm
        if iterations:
            self.iterations = iterations
        else:
            self.iterations = DEFAULT_ITER
        self.results = []
        self.fh = None
    
    def add_results(self, results):
        self.results.append()

    def run(self):
        self._run()
        with open('stats.txt', 'w') as self.fh:
            self.print_stats()

    def _run(self):
        print("Running {} iterations.".format(self.iterations))
        start = datetime.datetime.now()
        for i in range(self.iterations):
            if i and not i % 5000:
                print("Completed {} iterations.".format(i))
            t = tourney.Tournament(self.year, self.winner, self.second,
                                   self.madness, self.algorithm)
            self.results.append(t())
        done = datetime.datetime.now()
        duration = done-start
        print("Time to run: {} days {} seconds".format(duration.days, duration.seconds))

    def _print(self,text):
        self.fh.write("{}\n".format(text))
        print(text)

    def print_stats(self):
        upset_total = 0
        print("\nCalculating upsets...")
        for r in self.results:
            upset_total += upsets(self.year, r)
        average = upset_total/self.iterations
        self._print("Average upsets: {}\n".format(average))
        self.print_winners()

    def print_winners(self):
        winners = {}
        print("Calculating top winners")
        for r in self.results:
            if winners.get(r['champion'].name):
                winners[r['champion'].name]['count'] += 1
            else:
                winners[r['champion'].name] = {'team':r['champion'], 'count':1}

        sorted_winners = sorted(winners.items(), key=lambda x: x[1], reverse=True)

        for winner in sorted_winners:
            self._print("{}: {}/{} ({}%)".format(winner[1]['team'],
                                                 winner[1]['count'],
                                                 self.iterations,
                                                 float(winner[1]['count'])/float(self.iterations)*100))
