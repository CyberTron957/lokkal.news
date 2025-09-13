from django.core.management.base import BaseCommand
from news_app.models import Area

class Command(BaseCommand):
    help = 'Checks the geocoding status of all Area objects.'

    def handle(self, *args, **options):
        all_areas = Area.objects.all()
        mapped_areas = []
        unmapped_areas = []

        for area in all_areas:
            if area.latitude is not None and area.longitude is not None:
                mapped_areas.append(area)
            else:
                unmapped_areas.append(area)

        self.stdout.write(self.style.SUCCESS('--- Mapped Areas ---'))
        if mapped_areas:
            for area in mapped_areas:
                self.stdout.write(f'- {area.name} ({area.latitude}, {area.longitude})')
        else:
            self.stdout.write('No mapped areas found.')

        self.stdout.write(self.style.WARNING('\n--- Unmapped Areas ---'))
        if unmapped_areas:
            for area in unmapped_areas:
                self.stdout.write(f'- {area.name}')
        else:
            self.stdout.write('All areas have been mapped.')
