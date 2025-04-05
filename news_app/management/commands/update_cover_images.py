# news_app/management/commands/update_cover_images.py
from django.core.management.base import BaseCommand
from django.conf import settings # Import settings if needed for API keys etc.
import os # Import os if using environment variables in fetch_cover_image

# Adjust the import path based on your project structure if models/views are elsewhere
from news_app.models import Article
from news_app.views import fetch_cover_image

class Command(BaseCommand):
    help = 'Updates cover images for all existing articles using the fetch_cover_image function with keyword extraction.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to update cover images for all articles...")
        articles = Article.objects.all()
        updated_count = 0
        failed_count = 0
        skipped_count = 0

        total_articles = articles.count()
        self.stdout.write(f"Found {total_articles} articles to process.")

        for i, article in enumerate(articles):
            self.stdout.write(f"Processing article {i+1}/{total_articles}: '{article.title}' (ID: {article.id})")
            try:
                query = article.title
                category = article.category

                if not query:
                    self.stdout.write(f"  Skipping article ID {article.id} due to empty title.")
                    skipped_count += 1
                    continue

                # Ensure the UNSPLASH_ACCESS_KEY environment variable is set if you used that method
                # in fetch_cover_image. If hardcoded, ensure it's correct.
                new_image_url = fetch_cover_image(query, category)

                if new_image_url:
                    if new_image_url != article.cover_image:
                        self.stdout.write(f"  Found new image: {new_image_url}")
                        article.cover_image = new_image_url
                        # Save only the cover_image field for efficiency
                        article.save(update_fields=['cover_image'])
                        updated_count += 1
                    else:
                        self.stdout.write(f"  Fetched image is the same as the existing one. No update needed.")
                        # Optionally count this as skipped or just ignore
                else:
                    self.stdout.write(f"  Could not fetch a new image for query: '{query}'. Keeping existing image (if any).")
                    failed_count += 1 # Count cases where fetch failed or returned None

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Error processing article ID {article.id}: {e}")) # type: ignore
                failed_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nFinished updating cover images. "
            f"Total: {total_articles}, Updated: {updated_count}, "
            f"Fetch Failed: {failed_count}, Skipped (e.g., no title): {skipped_count}"
        ))
