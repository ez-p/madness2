"""
Copyright 2016, Paul Powell, All rights reserved.
"""
import random
from tournament.engine.algorithms.matchup import Matchup

#
# Implement a matchup between two teams
# Different algorithms can be created as long as the class implementation:
# 1) Takes a tuple of Team objects and a madness variable in contructor
# 2) Implements a 'play' method that returns a tuple of (winner,loser) Team objects
#
# Notes:
#   This algorithm uses the difference between the seeds as the probability one team
#   will beat a different team.  For example, there is a small chance that a #1 seed
#   will loose to a #16 seed.  In this algorithm, the #16 is given a 1 in 15 chances.
#   A #3 seed vs a #6 seed will get a 1 in 4 chance since the calculation is:
#
#     Create a range of numbers between seeds: [3, 4, 5]
#     Randomly select a number between 3-6
#     The lesser team wins only when the random number is 6, which is the only number
#     that can be selected that is not in the list.
#
#     Another example #2 vs #8:
#        Range is [2,3,4,5,6,7]
#        Select a random number betwee 2-8
#        If random number is 8, then lesser team wins
#
#   The chance of winning is adjusted by:
#      madness: The level of madness introduced in the tournament
#        power: The power level of the team
#
#   Madness adjusts the lesser teams chance of winning up by decreasing the range of
#   of numbers in the range list, thus introducing some madness in the tournament.
#
#   By default madness is set to one, which represents the 'average' amount of madness.
#   Meaning for a large number of runs, the madness converages to the average.
#
#   Power adjusts a teams chance of winning by moving the opponents seed up.
#     Example #1 vs #2 (#1 has power of 1, as it a very dominant team)
#        Opponents seed is adjusted up by 1, so now it is essentially #1 vs #3.
#        Therefore, #1 seed has an even better chance of winning.
#        
#     Example #3 vs #8 (#8 has power of 1)
#        Opponents seed is adjusted up by 1, so now it is #4 vs #8
#        Therefore, #3's advantage has shrunk
#
class SeedOddsMatchup(Matchup):
    # teams: tuple of Team objects (Team1, Team2)
    # madness: level of madness
    def __init__(self, teams, madness):
        super(SeedOddsMatchup, self).__init__(teams)

        # Keep track of a "madness seed" that we can adjust using
        # the madness level.
        self.team1 = {'team':teams[0],
                      'mad_seed':teams[0].seed,
                      'sf':teams[0].sf}
        self.team2 = {'team':teams[1],
                      'mad_seed':teams[1].seed,
                      'sf':teams[1].sf}

        # Adjust a teams seed based on power rating
        # Since we don't want negative numbers, we adjust opponents seed up
        # by opponents power, rather than adjust a team's seed down by power
        # Example: team1 has power level 1
        #          original team1.seed = 1, team2.seed = 12
        #          adjusted team1.seed = 1, team2.seed = 13
        self.team1['mad_seed'] = self.team1['mad_seed'] + self.team2['team'].power
        self.team2['mad_seed'] = self.team2['mad_seed'] + self.team1['team'].power

        self.madness = madness

    def _coin_flip(self, highseed, lowseed):
        winner = None
        loser = None
        seq = [1,2]
        val = random.choice(seq)
        if val == 1:
            winner = self.team1['team']
            loser = self.team2['team']
        else:
            winner = self.team2['team']
            loser = self.team1['team']
        return (winner, loser)

    def _play(self, madness):
        # See if superclass wants to handle the matchup
        status, self.winner, self.loser = Matchup.base_play(self.team1['team'],
                                                            self.team2['team'])
        if status:
            # Superclass handled the matchup
            return (self.winner, self.loser)

        # High seed is seed with larger number (worse)
        # Low seed is seed with smaller number (better team)
        highseed = self.team1
        lowseed = self.team2
        
        if lowseed['mad_seed'] > highseed['mad_seed']:
            highseed = self.team2
            lowseed = self.team1

        # Seeds are the same, coin flip
        if highseed['mad_seed'] == lowseed['mad_seed']:
            self.winner,self.loser = self._coin_flip(highseed,lowseed)
            return (self.winner, self.loser)

        # Seeds are off by one, coin flip
        if highseed['mad_seed'] - lowseed['mad_seed'] == 1:
            self.winner,self.loser = self._coin_flip(highseed,lowseed)
            return (self.winner, self.loser)

        if madness:
            # Adjust lowseed (which is the better team) up a notch
            lowseed['mad_seed'] = lowseed['mad_seed'] + 1
            return self._play(madness-1)

        highrange = range(lowseed['mad_seed'],highseed['mad_seed'])
        r = random.randrange(lowseed['mad_seed'],highseed['mad_seed']+1)

        if r in highrange:
            self.winner = lowseed['team']
            self.loser = highseed['team']
        else:
            self.winner = highseed['team']
            self.loser = lowseed['team']

        return (self.winner, self.loser)
