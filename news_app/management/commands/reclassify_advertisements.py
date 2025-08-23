from django.core.management.base import BaseCommand
from news_app.models import Advertisement
from news_app.views import categorize_advertisement
import time


class Command(BaseCommand):
    help = 'Reclassify all existing advertisements using the updated categorization logic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of advertisements to process in each batch (default: 10)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay in seconds between processing each advertisement (default: 1.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--area',
            type=str,
            help='Only reclassify advertisements from a specific area'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        dry_run = options['dry_run']
        area_filter = options['area']
        
        advertisements = Advertisement.objects.all()
        
        # Filter by area if specified
        if area_filter:
            advertisements = advertisements.filter(area__name__iexact=area_filter)
            area_message = f' in area "{area_filter}"'
        else:
            area_message = ''
        
        total_count = advertisements.count()
        
        if total_count == 0:
            if area_filter:
                self.stdout.write(
                    self.style.WARNING(f'No advertisements found in area "{area_filter}".')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No advertisements found to reclassify.')
                )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {total_count} advertisements{area_message} to reclassify.')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made.')
            )
        
        processed = 0
        updated = 0
        errors = 0
        
        for i in range(0, total_count, batch_size):
            batch = advertisements[i:i + batch_size]
            
            self.stdout.write(
                f'Processing batch {i//batch_size + 1} '
                f'(advertisements {i+1}-{min(i+batch_size, total_count)} of {total_count})'
            )
            
            for ad in batch:
                try:
                    old_category = ad.category
                    new_category = categorize_advertisement(ad.content)
                    
                    if old_category != new_category:
                        if not dry_run:
                            ad.category = new_category
                            ad.save(update_fields=['category'])
                        
                        self.stdout.write(
                            f'  Advertisement ID {ad.id}: "{old_category}" -> "{new_category}"'
                        )
                        updated += 1
                    else:
                        self.stdout.write(
                            f'  Advertisement ID {ad.id}: No change needed ("{old_category}")'
                        )
                    
                    processed += 1
                    
                    # Add delay to avoid overwhelming the API
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  Error processing advertisement ID {ad.id}: {str(e)}'
                        )
                    )
                    errors += 1
                    processed += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'SUMMARY:')
        self.stdout.write(f'  Total processed: {processed}')
        self.stdout.write(f'  Updated: {updated}')
        self.stdout.write(f'  Errors: {errors}')
        self.stdout.write(f'  Unchanged: {processed - updated - errors}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a dry run. Use without --dry-run to apply changes.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nReclassification completed!')
            )