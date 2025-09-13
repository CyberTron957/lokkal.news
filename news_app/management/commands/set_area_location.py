from django.core.management.base import BaseCommand, CommandError
from news_app.models import Area

class Command(BaseCommand):
    help = 'Manually sets the latitude and longitude for a specific area.'

    def add_arguments(self, parser):
        parser.add_argument('area_name', type=str, help='The name of the area to update.')
        parser.add_argument('latitude', type=float, help='The latitude of the area.')
        parser.add_argument('longitude', type=float, help='The longitude of the area.')

    def handle(self, *args, **options):
        area_name = options['area_name']
        latitude = options['latitude']
        longitude = options['longitude']

        try:
            area = Area.objects.get(name=area_name)
        except Area.DoesNotExist:
            raise CommandError(f'Area "{area_name}" does not exist.')

        area.latitude = latitude
        area.longitude = longitude
        area.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully updated location for "{area_name}" to ({latitude}, {longitude}).'))
