#!/usr/bin/env python
"""
Simple test script to verify advertisement functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DynamicAIWebsites.settings')
django.setup()

from news_app.models import Area, Advertisement
from news_app.views import categorize_advertisement

def test_advertisement_creation():
    """Test creating advertisements and categorization"""
    print("Testing Advertisement Creation and Categorization...")
    
    # Create or get a test area
    area, created = Area.objects.get_or_create(name="test area")
    print(f"Area: {area.name} ({'created' if created else 'exists'})")
    
    # Test advertisements with different categories
    test_ads = [
        {
            'content': 'Looking for a software developer position in tech company. 5 years experience in Python and Django.',
            'advertiser_name': 'John Developer',
            'expected_category': 'jobs'
        },
        {
            'content': '2 bedroom apartment for rent. $1200/month, near downtown, parking included.',
            'advertiser_name': 'Property Manager',
            'expected_category': 'housing'
        },
        {
            'content': 'Selling used iPhone 13, excellent condition, $400. Contact for details.',
            'advertiser_name': 'Tech Seller',
            'expected_category': 'for-sale'
        },
        {
            'content': 'Professional web design services. Custom websites for small businesses.',
            'advertiser_name': 'Web Designer',
            'expected_category': 'services'
        },
        {
            'content': 'Community book club meeting every Tuesday at 7pm. All welcome!',
            'advertiser_name': 'Book Club',
            'expected_category': 'community'
        }
    ]
    
    for i, ad_data in enumerate(test_ads, 1):
        print(f"\nTest {i}: Creating advertisement...")
        print(f"Content: {ad_data['content'][:50]}...")
        
        # Test categorization
        category = categorize_advertisement(ad_data['content'])
        print(f"AI Categorized as: {category}")
        print(f"Expected: {ad_data['expected_category']}")
        
        # Create advertisement
        ad = Advertisement.objects.create(
            content=ad_data['content'],
            advertiser_name=ad_data['advertiser_name'],
            area=area,
            category=category
        )
        
        print(f"Advertisement created with ID: {ad.pk}, Slug: {ad.slug}")
    
    # Display summary
    print(f"\n--- Summary ---")
    print(f"Total advertisements created: {Advertisement.objects.filter(area=area).count()}")
    
    # Group by category
    categories = Advertisement.objects.filter(area=area).values_list('category', flat=True).distinct()
    for category in categories:
        count = Advertisement.objects.filter(area=area, category=category).count()
        print(f"{category.title()}: {count} ads")

def test_advertisement_retrieval():
    """Test retrieving advertisements by category"""
    print("\n\nTesting Advertisement Retrieval...")
    
    area = Area.objects.get(name="test area")
    
    # Get all categories
    categories = Advertisement.objects.filter(area=area).values_list('category', flat=True).distinct()
    
    for category in categories:
        ads = Advertisement.objects.filter(area=area, category=category).order_by('-created_at')
        print(f"\n{category.title()} ({ads.count()} ads):")
        for ad in ads:
            print(f"  - {ad.content[:60]}... by {ad.advertiser_name or 'Anonymous'}")

if __name__ == "__main__":
    try:
        test_advertisement_creation()
        test_advertisement_retrieval()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()