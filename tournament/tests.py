"""
Copyright 2016, Paul Powell, All rights reserved.
"""
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from django.test import TestCase

import tournament.models as models
from tournament.engine.tourney import Tournament as EngineTournament
from tournament.engine.algorithms.fiftyfifty import FiftyFifty
from tournament.engine.algorithms.seedodds import SeedOddsMatchup


class EngineSimulationTests(TestCase):
    """
    Phase 0 baseline: the engine can run a full tournament to completion
    (independent of the web/view layer) for both bundled algorithms.
    """
    @classmethod
    def setUpTestData(cls):
        call_command('import')

    def test_seedodds_produces_a_champion(self):
        results = EngineTournament('2017', None, None, 1, SeedOddsMatchup)()
        self.assertIsNotNone(results['champion'])
        self.assertIsNotNone(results['2nd_place'])
        self.assertIn('south', results)
        self.assertIn('west', results)
        self.assertIn('east', results)
        self.assertIn('midwest', results)

    def test_fiftyfifty_produces_a_champion(self):
        results = EngineTournament('2017', None, None, 1, FiftyFifty)()
        self.assertIsNotNone(results['champion'])
        self.assertIsNotNone(results['2nd_place'])


class ImportCommandTests(TestCase):
    """
    Phase 0 baseline: the `import` management command populates
    Year/Team/RegionData (and Algorithm) from the bundled _data_* modules.
    """
    def test_import_populates_years_teams_regiondata_algorithms(self):
        call_command('import')

        self.assertEqual(models.Year.objects.count(), 3)
        self.assertEqual(models.Algorithm.objects.count(), 2)

        year_2017 = models.Year.objects.get(year='2017')
        self.assertEqual(
            models.RegionData.objects.filter(year=year_2017).count(), 4)
        self.assertEqual(
            models.Team.objects.filter(year=year_2017).count(), 64)

        # Final Four / exclusive-region relationships got wired up too.
        east = models.RegionData.objects.get(year=year_2017, name='east')
        self.assertEqual(east.ff_match.name, 'west')
        self.assertEqual(east.exclusive.name, 'west')


class CoreViewTests(TestCase):
    """
    Phase 0 baseline: golden-path views render and behave as expected,
    including the options-form region validation errors.
    """
    @classmethod
    def setUpTestData(cls):
        call_command('import')
        cls.year = models.Year.objects.get(year='2017')
        cls.seedodds = models.Algorithm.objects.get(name='Seed Odds')

    def test_home_page(self):
        response = self.client.get(reverse('home-page'))
        self.assertEqual(response.status_code, 200)

    def test_generate_tournament_and_view_result(self):
        response = self.client.get(reverse('run-tournament'))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)

    def test_create_with_options_same_region_validation_error(self):
        winner = models.Team.objects.get(
            year=self.year, name='North Carolina')  # south
        second = models.Team.objects.get(
            year=self.year, name='Kentucky')  # south

        response = self.client.post(reverse('create-with-options'), {
            'year': self.year.pk,
            'madness': 1,
            'algorithm': self.seedodds.pk,
            'winner': winner.pk,
            'second': second.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cannot be in the same region')

    def test_create_with_options_mutually_exclusive_validation_error(self):
        winner = models.Team.objects.get(year=self.year, name='Villanova')  # east
        second = models.Team.objects.get(year=self.year, name='Gonzaga')  # west

        response = self.client.post(reverse('create-with-options'), {
            'year': self.year.pk,
            'madness': 1,
            'algorithm': self.seedodds.pk,
            'winner': winner.pk,
            'second': second.pk,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cannot play each other in the championship')

    def test_register_login_logout(self):
        response = self.client.post(reverse('register'), {
            'username': 'tester',
            'password1': 'a-pretty-good-pw-9',
            'password2': 'a-pretty-good-pw-9',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='tester').exists())

        self.client.logout()

        response = self.client.post(reverse('login'), {
            'username': 'tester',
            'password': 'a-pretty-good-pw-9',
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('logout'))
        self.assertIn(response.status_code, (200, 302))
