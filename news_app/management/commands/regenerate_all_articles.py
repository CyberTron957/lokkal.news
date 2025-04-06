# news_app/management/commands/regenerate_all_articles.py

import time
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from news_app.models import Area, Article, Post
# Import necessary functions from views.py
from news_app.views import get_posts_content_by_area, run_gemini, fetch_cover_image

class Command(BaseCommand):
    help = 'Regenerates news articles for ALL areas, ignoring the last_generated_at timestamp.'

    def add_arguments(self, parser):
        # Optional: Add an argument to run for specific areas only
        parser.add_argument(
            '--area-names',
            nargs='+',
            type=str,
            help='Specify one or more area names to regenerate articles for. If not provided, regenerates for all areas.',
        )
        parser.add_argument(
            '--skip-existing-check',
            action='store_true',
            help='Generate new articles even if articles already exist for the area.',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        total_areas_processed = 0
        total_articles_created = 0

        area_names_filter = options['area_names']
        skip_existing = options['skip_existing_check']

        if area_names_filter:
            areas_to_process = Area.objects.filter(name__in=[name.lower() for name in area_names_filter])
            self.stdout.write(f"Regenerating articles for specified areas: {', '.join(area_names_filter)}")
        else:
            areas_to_process = Area.objects.all()
            self.stdout.write("Regenerating articles for ALL areas...")

        if not areas_to_process.exists():
            self.stdout.write(self.style.WARNING("No areas found matching the criteria."))
            return

        for area in areas_to_process:
            total_areas_processed += 1
            self.stdout.write(f"\nProcessing Area: {area.name} (PK: {area.pk})")

            # Check if articles already exist and skip if needed
            if not skip_existing and area.articles.exists(): # type: ignore
                 self.stdout.write(self.style.NOTICE(f"  Skipping area '{area.name}' as articles already exist. Use --skip-existing-check to override."))
                 continue

            # Fetch ALL posts for this area, ignoring 'since'
            all_comments = get_posts_content_by_area(area.name) # Pass area name directly

            if not all_comments:
                self.stdout.write(f"  No posts found for area '{area.name}'. Skipping article generation.")
                continue

            self.stdout.write(f"  Found {len(all_comments.split('\" \"'))} posts. Sending content to LLM...") # Approximate post count

            # Generate articles using the existing function
            articles_data = run_gemini(all_comments)

            if not articles_data:
                self.stdout.write(self.style.WARNING(f"  LLM did not return any articles for '{area.name}'."))
                continue

            self.stdout.write(f"  LLM generated {len(articles_data)} articles.")
            area_articles_created = 0
            for article_data in articles_data:
                title = article_data.get('title')
                content = article_data.get('content')

                if not title or not content:
                    self.stdout.write(self.style.WARNING("  Skipping article data with missing title or content."))
                    continue

                category = article_data.get('category', 'news')
                # Fetch cover image using the existing function
                cover_image_url = fetch_cover_image(title, category)

                try:
                    article = Article.objects.create(
                        title=title,
                        content=content,
                        category=category,
                        cover_image=cover_image_url,
                        area=area # Directly associate with the current Area object
                    )
                    area_articles_created += 1
                    total_articles_created += 1
                    # Use article.pk for clarity
                    self.stdout.write(f"    Created article: '{article.title}' (PK: {article.pk})")
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"    Error creating article '{title}': {e}"))

            self.stdout.write(self.style.SUCCESS(f"  Finished processing '{area.name}'. Created {area_articles_created} new articles."))
            # We are NOT updating area.last_generated_at here to allow normal generation later

        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(f"\n--------------------")
        self.stdout.write(self.style.SUCCESS(f"Regeneration Complete!"))
        self.stdout.write(f"Processed {total_areas_processed} areas.")
        self.stdout.write(f"Created a total of {total_articles_created} articles.")
        self.stdout.write(f"Duration: {duration:.2f} seconds.")
