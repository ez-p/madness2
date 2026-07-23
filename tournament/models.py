"""
Copyright 2016, Paul Powell, All rights reserved.
"""
from django.db import models
from django.contrib.auth.models import User

## **********************************************
## Static data representing the tournament format
## **********************************************
class Year(models.Model):
    year = models.CharField(max_length=8)

    def __str__(self):
        return "{}".format(self.year)

# A Region (south, east, midwest, or west)
class RegionData(models.Model):
    name = models.CharField(max_length=32)
    ff_match = models.ForeignKey('self', related_name='my_ff_match', null=True, on_delete=models.CASCADE)
    exclusive = models.ForeignKey('self', related_name='my_exclusive', null=True, on_delete=models.CASCADE)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)

    def __str__(self):
        return "{} {}".format(self.year.year, self.name.capitalize())

# Represent a team in the tournament
class Team(models.Model):
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    region = models.ForeignKey(RegionData, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    seed = models.IntegerField()
    power = models.IntegerField(default=0)
    
    def str_name_seed(self):
        return "{} [{}]".format(self.name, self.seed)

    def __str__(self):
        return "({}) {} [{}]".format(self.region, self.name, self.seed)

class Algorithm(models.Model):
    name = models.CharField(max_length=128)
    
    def __str__(self):
        return self.name

## **********************************************
## Dynamic data produced by tournament simulation
## **********************************************
class Options(models.Model):
    year = models.ForeignKey(Year, blank=False, default='', on_delete=models.CASCADE)
    madness = models.PositiveIntegerField(default=1)
    winner = models.ForeignKey(Team, blank=True, null=True, related_name="winner", on_delete=models.CASCADE)
    second = models.ForeignKey(Team, blank=True, null=True, related_name="second", on_delete=models.CASCADE)
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)

class Tournament(models.Model):
    user = models.ForeignKey(
            User,
            on_delete=models.SET_NULL,
            null=True)
    date = models.DateTimeField(auto_now_add=True)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    winner = models.ForeignKey(Team, related_name="+", on_delete=models.CASCADE)
    runnerup = models.ForeignKey(Team, related_name="+", on_delete=models.CASCADE)
    upsets = models.IntegerField(default=0)
    options = models.ForeignKey(Options, on_delete=models.CASCADE)

    def __str__(self):
        return "({}) vs {}".format(self.winner, self.runnerup)

class Region(models.Model):
    name = models.CharField(max_length=32)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    def __str__(self):
        return "({}) {}".format(self.tournament.year.year, self.name)
    
    @property
    def winner(self):
        for r in self.round_set.all():
            if r.matchup_set.count() == 1:
                return r.matchup_set.all()[0].winner 
    
    @property
    def loser(self):
        for r in self.round_set.all():
            if r.matchup_set.count() == 1:
                return r.matchup_set.all()[0].loser

    @property
    def rounds(self):
        """
        This is used to make sure the pretty printing of the tournament
        in the full view prints the rounds in the correct order.
        """
        rnds = {}
        for round in self.round_set.all():
            rnds[round.matchup_set.all().count()] = round
        return rnds

class Round(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

class Matchup(models.Model):
    team1 = models.ForeignKey(Team, related_name="+", on_delete=models.CASCADE)
    team2 = models.ForeignKey(Team, related_name="+", on_delete=models.CASCADE)
    winner = models.ForeignKey(Team, related_name="+", on_delete=models.CASCADE)
    round = models.ForeignKey(Round, null=True, on_delete=models.CASCADE)
    # Populated only if a final four matchup
    tournament = models.ForeignKey(Tournament, related_name="semis", null=True, on_delete=models.CASCADE)

    @property
    def loser(self):
        if self.winner == self.team1:
            return self.team2
        return self.team1
