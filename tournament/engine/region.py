"""
Copyright 2016, Paul Powell, All rights reserved.
"""
from tournament.engine import team, round

class Region:
    def __init__(self, name, teams, algorithm):
        self.initialize(name, teams)
        self.name = name
        self.rounds = []
        self.algorithm = algorithm
        self.final = None

    def __call__(self, madness):
        round1 = round.Round(self.name, 1, madness, self.algorithm, self.matchups)
        round2 = round1.go()
        round3 = round2.go()
        round4 = round3.go()
        self.rounds = [round1, round2, round3, round4]

        # Special hacks for final round
        self.final = self.algorithm(round4.games[0], madness)
        round4.winner = self.final.winner
        round4.results.append(self.final)
        return self.final()[0]

    def initialize(self, name, teams):
        # Looks like [((1,16), (8,9)), ((5,12), (4,13)), ((6,11), (3,14)), ((7,10), (2,15))]
        sregion = name
        game1 = (team.Team(teams[1], sregion, 1), team.Team(teams[16], sregion, 16))
        game2 = (team.Team(teams[8], sregion, 8), team.Team(teams[9], sregion, 9))
        game3 = (team.Team(teams[5], sregion, 5), team.Team(teams[12], sregion, 12))
        game4 = (team.Team(teams[4], sregion, 4), team.Team(teams[13], sregion, 13))
        game5 = (team.Team(teams[6], sregion, 6), team.Team(teams[11], sregion, 11))
        game6 = (team.Team(teams[3], sregion, 3), team.Team(teams[14], sregion, 14))
        game7 = (team.Team(teams[7], sregion, 7), team.Team(teams[10], sregion, 10))
        game8 = (team.Team(teams[2], sregion, 2), team.Team(teams[15], sregion, 15))
        self.matchups = [(game1, game2), (game3, game4), (game5, game6), (game7, game8)]

    def set_sf(self, winner, second):
        for matchup in self.matchups:
            for game in matchup:
                for team in game:
                    if team.name == winner:
                        print("found winner")
                        team.sf = 3
                    if team.name == second:
                        print("found second")
                        team.sf = 2
