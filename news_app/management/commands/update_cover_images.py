# news_app/management/commands/update_cover_images.py
import time
from django.core.management.base import BaseCommand
from django.db.models import Q
from news_app.models import Article
# Import the function directly from views.py
# Consider moving fetch_cover_image to a utils.py file for better organization later
from news_app.views import fetch_cover_image

class Command(BaseCommand):
    help = 'Fetches and updates cover images for articles where the cover_image field is null or empty.'

    def handle(self, *args, **options):
        # Find articles with null or empty cover_image field
        articles_to_update = Article.objects.filter(
            Q(cover_image__isnull=True) | Q(cover_image='')
        )

        total_articles = articles_to_update.count()
        if total_articles == 0:
            self.stdout.write(self.style.SUCCESS('All articles already have a cover image.'))
            return

        self.stdout.write(f'Found {total_articles} articles needing cover images. Attempting to fetch...')

        updated_count = 0
        failed_count = 0
        api_delay = 1 # Seconds delay between Unsplash API calls to avoid rate limiting

        for article in articles_to_update:
            self.stdout.write(f"\nProcessing Article (PK: {article.pk}): '{article.title}'")
            try:
                # Call the existing function from views.py
                image_url = fetch_cover_image(article.title, article.category)

                if image_url:
                    article.cover_image = image_url
                    article.save(update_fields=['cover_image'])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  Successfully updated cover image."))
                else:
                    # fetch_cover_image function already prints details on failure
                    self.stdout.write(self.style.WARNING(f"  Could not find a suitable cover image."))
                    failed_count +=1

                # Add a delay to prevent hitting API rate limits
                time.sleep(api_delay)

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"  An error occurred while processing article {article.pk}: {e}"))
                # Optional: Add a longer sleep after an error
                # time.sleep(api_delay * 5)


        self.stdout.write("\n" + "="*30)
        self.stdout.write(self.style.SUCCESS(f'Finished processing.'))
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} cover images.'))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f'{failed_count} articles could not be updated (no image found or error occurred).'))
        self.stdout.write("="*30)
