#!/usr/bin/env python
"""
Simple script to create test advertisements without using Gemini API
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DynamicAIWebsites.settings')
django.setup()

from news_app.models import Area, Advertisement

def create_test_advertisements():
    """Create test advertisements with predefined categories"""
    print("Creating test advertisements...")
    
    # Create or get a test area
    area, created = Area.objects.get_or_create(name="test area")
    print(f"Area: {area.name} ({'created' if created else 'exists'})")
    
    # Test advertisements with predefined categories
    test_ads = [
        {
            'content': 'Looking for a software developer position in tech company. 5 years experience in Python and Django. Contact me at developer@email.com',
            'advertiser_name': 'John Developer',
            'category': 'jobs'
        },
        {
            'content': '2 bedroom apartment for rent. $1200/month, near downtown, parking included. Available immediately. Call 555-0123',
            'advertiser_name': 'Property Manager',
            'category': 'housing'
        },
        {
            'content': 'Selling used iPhone 13, excellent condition, $400. Original box and charger included. Contact for details.',
            'advertiser_name': 'Tech Seller',
            'category': 'for-sale'
        },
        {
            'content': 'Professional web design services. Custom websites for small businesses. Affordable rates, quick turnaround.',
            'advertiser_name': 'Web Designer',
            'category': 'services'
        },
        {
            'content': 'Community book club meeting every Tuesday at 7pm. All welcome! Currently reading "The Great Gatsby".',
            'advertiser_name': 'Book Club',
            'category': 'community'
        },
        {
            'content': 'Freelance graphic designer available for logo design, branding, and marketing materials. Portfolio available.',
            'advertiser_name': 'Creative Studio',
            'category': 'gigs'
        },
        {
            'content': 'Experienced marketing manager seeking new opportunities. 8+ years in digital marketing and social media.',
            'advertiser_name': 'Marketing Pro',
            'category': 'resumes'
        },
        {
            'content': 'Local hiking group meets every weekend. Join us for scenic trails and outdoor adventures!',
            'advertiser_name': 'Hiking Club',
            'category': 'community'
        },
        {
            'content': 'Vintage bicycle for sale. Classic 1980s road bike, well maintained. $300 or best offer.',
            'advertiser_name': 'Bike Enthusiast',
            'category': 'for-sale'
        },
        {
            'content': 'Tutoring services available for high school math and science. Experienced teacher, flexible schedule.',
            'advertiser_name': 'Math Tutor',
            'category': 'services'
        }
    ]
    
    created_count = 0
    for i, ad_data in enumerate(test_ads, 1):
        print(f"Creating advertisement {i}: {ad_data['content'][:50]}...")
        
        # Create advertisement with predefined category
        ad = Advertisement.objects.create(
            content=ad_data['content'],
            advertiser_name=ad_data['advertiser_name'],
            area=area,
            category=ad_data['category']
        )
        
        created_count += 1
        print(f"  ✓ Created with ID: {ad.pk}, Category: {ad.category}")
    
    # Display summary
    print(f"\n--- Summary ---")
    print(f"Total advertisements created: {created_count}")
    
    # Group by category
    categories = Advertisement.objects.filter(area=area).values_list('category', flat=True).distinct()
    for category in categories:
        count = Advertisement.objects.filter(area=area, category=category).count()
        print(f"  {category.title()}: {count} ads")
    
    return area

def display_advertisements(area):
    """Display all advertisements by category"""
    print(f"\n--- Advertisements in {area.name.title()} ---")
    
    categories = Advertisement.objects.filter(area=area).values_list('category', flat=True).distinct()
    
    for category in categories:
        ads = Advertisement.objects.filter(area=area, category=category).order_by('-created_at')
        print(f"\n{category.title()} ({ads.count()} ads):")
        for ad in ads:
            print(f"  • {ad.content[:60]}... by {ad.advertiser_name or 'Anonymous'}")

if __name__ == "__main__":
    try:
        area = create_test_advertisements()
        display_advertisements(area)
        print("\n✅ Test advertisements created successfully!")
        print(f"\nYou can now visit: http://127.0.0.1:8000/{area.name}/ to see the ads in action!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()