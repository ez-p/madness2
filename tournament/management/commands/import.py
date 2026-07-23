from django.core.management.base import BaseCommand

# If this import fails, softlink _data.py to _data_<year>.py
from tournament.models import *
class Command(BaseCommand):
    help = 'Import bracket information into the database'

    # Clear the database tables
    def delete_all(self):
        Year.objects.all().delete()
        RegionData.objects.all().delete()
        Team.objects.all().delete()
        Algorithm.objects.all().delete()

    def make_algorithms(self):
        a = Algorithm(name='Seed Odds')
        a.save()
        b = Algorithm(name='Fifty Fifty')
        b.save()
    
    def import_years(self):
        from tournament.management.commands import _data_2015 as data2015
        from tournament.management.commands import _data_2016 as data2016
        from tournament.management.commands import _data_2017 as data2017

        y = Year(year=data2015.year)
        y.save()

        y = Year(year=data2016.year)
        y.save()

        y = Year(year=data2017.year)
        y.save()

        return [data2015, data2016, data2017]

    # Import region data
    def import_regions(self, data):
        year = Year.objects.get(year=data.year)

        for region in data.all_regions:
            r = RegionData()
            r.name = region
            r.year = year
            r.save()

        for a,b in data.exclusives.items():
            r1 = RegionData.objects.filter(year=year).get(name=a)
            r2 = RegionData.objects.filter(year=year).get(name=b)
            r1.exclusive = r2
            r2.exclusive = r1
            r1.save()
            r2.save()

    # Import the Final Four matches - which regions play which
    def ff_format(self, data):
        year = Year.objects.get(year=data.year)

        for match in data.ff_games:
            # match is a tuple like ('east','midwest')
            r0 = RegionData.objects.filter(year=year).get(name=match[0])
            r1 = RegionData.objects.filter(year=year).get(name=match[1])
            r0.ff_match = r1
            r1.ff_match = r0
            r0.save()
            r1.save()

    def import_team_by_region(self, data, region):
        year = Year.objects.get(year=data.year)
        r = RegionData.objects.filter(year=year).get(name=region)
        rdata = data.all_regions[region]
        for seed in range(1,17):
            t = Team()
            t.name = rdata[seed]['name']
            t.seed = seed
            t.power = rdata[seed]['power']
            t.region = r
            t.year = year
            t.save()

    def import_teams(self, data):
        for region in data.all_regions:
            self.import_team_by_region(data, region)

    # Get'r done
    def handle(self, *args, **options):
        self.delete_all()
        self.make_algorithms()
        datas = self.import_years()
        for data in datas:
            self.import_regions(data)
            self.ff_format(data)
            self.import_teams(data)
