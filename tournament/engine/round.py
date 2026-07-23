"""
Copyright 2016, Paul Powell, All rights reserved.
"""
class Round:
    def __init__(self, region, number, madness, algorithm, games=[]):
       # List of tuples of tuples which describe current games and matchups in next round
       # Inside tuples are Teams
       # i.e. [((1,16), (8,9)), ((5,12), (4,13)), ((6,11), (3,14)), ((7,10), (2,15))]
       # but not just numbers, Team objects
       self.games = games
       self.region = region
       self.number = number
       self.madness = madness
       self.algorithm = algorithm
       self.results = []

    def add(self, matchup):
        self.games.append(matchup)

    def go(self):
        next_round = Round(self.region, self.number+1, self.madness,
                                self.algorithm, games=[])
        nextup = []
        for game in self.games:
            match1 = self.algorithm(game[0], self.madness)
            match2 = self.algorithm(game[1], self.madness)
            # Add a tuple representing next matchup
            m1 = match1()[0]
            m2 = match2()[0]
            nextup.append((m1,m2))
            self.results.append(match1)
            self.results.append(match2)
        
        if len(nextup) == 1:
            # Last game for region
            next_round.add(nextup[0])
            return next_round

        for i in range(0, len(nextup), 2):
            next_round.add((nextup[i], nextup[i+1]))
        return next_round
