from django.core.management.base import BaseCommand
from django.db.models import Q
from news_app.models import Area


class Command(BaseCommand):
    help = 'List areas that do not have latitude and/or longitude set.'

    def add_arguments(self, parser):
        parser.add_argument('--show-zero', action='store_true', help='Treat 0.0 as unmapped and include them in the result')

    def handle(self, *args, **options):
        show_zero = options.get('show_zero', False)

        if show_zero:
            unmapped = Area.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True) | Q(latitude=0.0) | Q(longitude=0.0))
        else:
            unmapped = Area.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))

        if not unmapped.exists():
            self.stdout.write(self.style.SUCCESS('All areas have latitude and longitude set.'))
            return

        self.stdout.write('Unmapped Areas:')
        for area in unmapped:
            lat = area.latitude if area.latitude is not None else 'NULL'
            lon = area.longitude if area.longitude is not None else 'NULL'
            area_id = getattr(area, 'id', getattr(area, 'pk', 'unknown'))
            self.stdout.write(f'- {area.name} (id={area_id}) -> lat: {lat}, lon: {lon}')
