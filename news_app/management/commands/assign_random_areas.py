# news_app/management/commands/assign_random_areas.py
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from news_app.models import Article, Area

class Command(BaseCommand):
    help = 'Assigns a random Area to articles that currently have no Area assigned.'

    def handle(self, *args, **options):
        articles_without_area = Article.objects.filter(area__isnull=True)
        all_areas = list(Area.objects.all())

        if not all_areas:
            self.stdout.write(self.style.ERROR('No Areas found in the database. Please create some Areas first.'))
            return

        if not articles_without_area.exists():
            self.stdout.write(self.style.SUCCESS('All articles already have an Area assigned.'))
            return

        count = 0
        total_articles = articles_without_area.count()
        self.stdout.write(f'Found {total_articles} articles without an Area. Assigning random Areas...')

        try:
            with transaction.atomic():
                for article in articles_without_area:
                    random_area = random.choice(all_areas)
                    article.area = random_area
                    article.save(update_fields=['area']) # More efficient save
                    count += 1
                    # Optional: Add progress output if dealing with many articles
                    # if count % 100 == 0:
                    #    self.stdout.write(f'Processed {count}/{total_articles} articles...')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            self.stdout.write(self.style.WARNING(f'Rolled back transaction. {count} articles were processed before the error.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Successfully assigned random Areas to {count} articles.'))
