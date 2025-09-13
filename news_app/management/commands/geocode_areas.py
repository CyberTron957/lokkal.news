
import requests
from django.core.management.base import BaseCommand
from news_app.models import Area
import time

class Command(BaseCommand):
    help = 'Geocodes existing Area objects that do not have latitude and longitude.'

    def add_arguments(self, parser):
        parser.add_argument('--context', type=str, help='A string to add to the geocoding query for context (e.g., ", Hyderabad, India").')
        parser.add_argument('--re-geocode-unmapped', action='store_true', help='Only geocode areas that are currently unmapped.')

    def handle(self, *args, **options):
        context = options['context'] or ''
        re_geocode_unmapped = options['re_geocode_unmapped']

        if re_geocode_unmapped:
            areas_to_geocode = Area.objects.filter(latitude__isnull=True, longitude__isnull=True)
            self.stdout.write(f"Found {areas_to_geocode.count()} unmapped areas to re-geocode.")
        else:
            areas_to_geocode = Area.objects.all()
            self.stdout.write(f"Geocoding all {areas_to_geocode.count()} areas.")

        for area in areas_to_geocode:
            self.stdout.write(f"Geocoding area: {area.name}")
            query = f"{area.name}{context}"
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
            try:
                response = requests.get(url, headers={'User-Agent': 'Gemini-CLI-Agent/1.0'})
                response.raise_for_status()
                data = response.json()
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    area.latitude = lat
                    area.longitude = lon
                    area.save()
                    self.stdout.write(self.style.SUCCESS(f"Successfully geocoded {area.name}: ({lat}, {lon})"))
                else:
                    self.stdout.write(self.style.WARNING(f"Could not find coordinates for {area.name}"))
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error geocoding {area.name}: {e}"))
            
            time.sleep(1)
