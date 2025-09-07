import time
from unicodedata import category
from .forms import PostForm, AdvertisementForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from .models import Article, Post, questions, URLModel, Area, Advertisement
from django.conf import settings
import google.generativeai as genai
import requests
import json
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Sum, F
from django.urls import resolve
from django.utils import timezone
from datetime import timedelta, datetime
from django.template import loader
import os
import re # Import regular expressions for cleaning
from difflib import SequenceMatcher # Import for string similarity
from gnews import GNews # Import for Google News API
import feedparser # Ensure this is imported
from bs4 import BeautifulSoup # Ensure this is imported
import urllib.parse # Ensure this is imported
from django.core.cache import cache # Import Django's cache
import logging
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# A simple list of common English stop words. You could expand this.
STOP_WORDS = set([
    "a", "an", "and", "are", "as", "at", "be", "but", "by",
    "for", "if", "in", "into", "is", "it",
    "no", "not", "of", "on", "or", "such",
    "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with", "over", "post-oc" # Added 'over' and 'post-oc' based on example
])

def normalize_area_name(name: str | None) -> str:
    """Converts to lowercase, strips whitespace, and collapses internal spaces."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name) # Replace multiple spaces with single space
    return name

def find_similar_area(input_name: str | None) -> dict | None:
    """Find the most similar area name in the database using string similarity."""
    if not input_name:
        return None
    normalized_input = normalize_area_name(input_name)
    # First try an exact match
    try:
        exact_match = Area.objects.get(name=normalized_input)
        return None  # No correction needed if exact match
    except Area.DoesNotExist:
        pass
    # If no exact match, find similar areas
    all_areas = Area.objects.all()
    best_match = None
    highest_ratio = 0.0
    # Lower similarity thresholds
    high_confidence_threshold = 0.7
    suggestion_threshold = 0.4
    for area in all_areas:
        similarity_ratio = SequenceMatcher(None, normalized_input, area.name).ratio()
        if similarity_ratio > highest_ratio and similarity_ratio >= suggestion_threshold:
            highest_ratio = similarity_ratio
            best_match = area
    if best_match and highest_ratio >= high_confidence_threshold:
        # High confidence match - autocorrect
        return {'area': best_match, 'confidence': 'high'}
    elif best_match:
        # Lower confidence match - suggest but don't autocorrect
        return {'area': best_match, 'confidence': 'low'}
    else:
        # No good match found
        return None

def run_gemini(text, area_name, max_retries=3, retry_delay=2):
    """
    Generate articles using Gemini API with retry logic for error recovery.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            schema = {
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "category": {"type": "string"},
                                "image_keywords": {"type": "string"},
                                "reporter_name": {"type": "string"}
                            },
                            "required": ["title", "content"]
                        }
                    }
                },
                "required": ["articles"]
            }

            model = genai.GenerativeModel( # type: ignore
                'gemini-2.5-flash',
                generation_config={"response_mime_type": "application/json",
                                   "response_schema": schema}
            )

            prompt = f"Based on the diverse comments collected from individuals in the area of {area_name}, please create a series of long engaging news articles. For each article, provide a title, content, category, image_keywords, and a reporter_name. The reporter_name should be credited to the individual if their name is provided, or use a general credit like 'A Community Report' if names are mixed or anonymous. Ensure article titles prominently feature the area name: '{area_name}'. Here are the comments: {text}"
            response = model.generate_content(prompt)
            parsed_data = json.loads(response.text)
            return parsed_data['articles']
        except Exception as e:
            logger.exception(f"Error in run_gemini (attempt {attempt+1}/{max_retries}): {e}")
            attempt += 1
            if attempt < max_retries:
                time.sleep(retry_delay)
    logger.error(f"run_gemini failed after {max_retries} attempts.")
    return []

def generate_article_qs(article):
    try:
        schema = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["questions"]
        }

        model = genai.GenerativeModel( # type: ignore
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json",
                               "response_schema": schema}
        )

        response = model.generate_content(f"As an AI tasked with enhancing community engagement, please generate 3  insightful very short questions ( under 10 words) based on the following article. These questions should encourage readers to share their own experiences or provide additional comments that could enrich the article: Title: {article.title}. Content: {article.content}")
        parsed_data = json.loads(response.text)
        return parsed_data['questions']
    except Exception as e:
        logger.exception(f"Error in generate_article_qs: {e}")
        return []

def fetch_cover_image(query, category=None):
    """
    Fetches a cover image from Unsplash based on a query and optional category.
    Filters stop words from the query for better relevance.
    Uses caching to avoid repeated API calls for the same query.
    """
    if not query:
        logger.error("Error: Empty query passed to fetch_cover_image.")
        return None

    # Clean the query: remove punctuation, convert to lowercase
    cleaned_query = re.sub(r'[^\w\s]', '', query.lower())
    words = cleaned_query.split()

    # Filter stop words
    keywords = [word for word in words if word not in STOP_WORDS]

    # Limit the number of keywords (e.g., max 5)
    keywords = keywords[:5]

    # Add category to keywords if provided and meaningful
    if category and category.lower() not in STOP_WORDS and category.lower() != 'news': # Avoid generic 'news'
         keywords.append(category.lower())

    # Create the final search query string
    if not keywords:
         # If all words were stop words, fall back to the first 2-3 original words
         simplified_query = " ".join(query.split()[:3])
         logger.info(f"No significant keywords found in '{query}'. Falling back to: '{simplified_query}'")
    else:
        simplified_query = " ".join(keywords)
        logger.info(f"Original query: '{query}', Category: '{category}', Keywords for search: '{simplified_query}'")

    # Create a cache key based on the simplified query
    cache_key = f"cover_image_cache_{urllib.parse.quote(simplified_query)}"
    cached_image_url = cache.get(cache_key)

    if cached_image_url:
        logger.info(f"  Returning cached image for '{simplified_query}': {cached_image_url}")
        return cached_image_url

    logger.info(f"  No cache hit for '{simplified_query}'. Fetching from API.")
    try:
        url = f"https://api.unsplash.com/search/photos"
        client_id = os.environ.get("UNSPLASH_ACCESS_KEY", "LSOUqV2JJVVQMYMapOqQdsMKkC1_Nrmu0w45m5NHpQc") # Use your actual key or env var
        params = {
            "query": simplified_query, # Use the keyword-based query
            "client_id": client_id,
            "per_page": 1,
            "orientation": "landscape"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            image_url = data["results"][0].get("urls", {}).get("regular")
            if image_url:
                logger.info(f"  Successfully fetched image: {image_url}")
                # Cache the result for 24 hours (86400 seconds)
                cache.set(cache_key, image_url, timeout=86400)
                return image_url
            else:
                logger.info("  No regular URL found in the first image result.")
        else:
            logger.info(f"  No image results found for query: '{simplified_query}'")
    except requests.exceptions.RequestException as e:
        logger.error(f"  Error fetching image from Unsplash: {e}")
    except Exception as e:
        logger.exception(f"  An unexpected error occurred: {e}")

    # Cache a None result for a shorter period (e.g., 1 hour) to avoid hammering API for non-existent images
    cache.set(cache_key, None, timeout=3600)
    return None # Return None if anything goes wrong or no image is found


def init_view(request):
    if request.method == 'POST':
        original_input = request.POST.get('area', '')
        skip_correction = request.POST.get('skip_correction') == 'true'
        
        logger.info(f"POST request with area: '{original_input}', skip_correction: {skip_correction}")
        area_name = normalize_area_name(original_input)
        logger.info(f"Normalized area name: '{area_name}'")
        
        if not area_name:
            messages.error(request, "Area name cannot be empty.")
            return redirect('enter_area')

        if skip_correction:
            area, created = Area.objects.get_or_create(name=area_name)
            logger.info(f"Skip correction. Area: '{area.name}', Created: {created}")
            # Clear any correction session variables if user explicitly searched
            request.session.pop('auto_corrected', None)
            request.session.pop('suggestion_only', None)
            request.session.pop('original_query', None)
            request.session.pop('corrected_query', None)
            return redirect(f'/{area_name}/')
            
        try:
            area = Area.objects.get(name=area_name)
            # Clear any correction session variables if exact match found
            request.session.pop('auto_corrected', None)
            request.session.pop('suggestion_only', None)
            request.session.pop('original_query', None)
            request.session.pop('corrected_query', None)
            return redirect(f'/{area_name}/')
        except Area.DoesNotExist:
            similar_result = find_similar_area(area_name)
            
            if similar_result:
                similar_area_obj = similar_result['area']
                confidence = similar_result['confidence']
                
                request.session['original_query'] = original_input # The actual user input
                request.session['corrected_query'] = similar_area_obj.name # The suggestion

                if confidence == 'high':
                    request.session['auto_corrected'] = True
                    request.session['suggestion_only'] = False
                    logger.info(f"High confidence. Redirecting to suggested: '{similar_area_obj.name}' for input '{original_input}'")
                    return redirect(f'/{similar_area_obj.name}/')
                else: # Low confidence (suggestion_only)
                    request.session['auto_corrected'] = False
                    request.session['suggestion_only'] = True
                    # Create the originally searched (potentially typo) area if it doesn't exist
                    # This ensures the user lands on the page they typed, with a suggestion.
                    area, created = Area.objects.get_or_create(name=area_name) 
                    logger.info(f"Low confidence. User searched for '{area_name}' (created: {created}), suggesting '{similar_area_obj.name}'.")
                    return redirect(f'/{area_name}/')
            else:
                # No exact match, no similar area found. Create the new area.
                area = Area.objects.create(name=area_name)
                logger.info(f"No match, no suggestion. Creating new area: '{area.name}'")
                # Clear any correction session variables
                request.session.pop('auto_corrected', None)
                request.session.pop('suggestion_only', None)
                request.session.pop('original_query', None)
                request.session.pop('corrected_query', None)
                return redirect(f'/{area_name}/')
   
    # Get the top areas based on the SUM of visits of their associated non-article URLModels
    top_areas = Area.objects.annotate(
        total_visits=Sum(
            'urlmodel__visits', 
            filter=Q(urlmodel__article__isnull=True) # Only count visits for area pages, not articles
        )
    ).filter(
        total_visits__isnull=False # Ensure the area has associated page visits
    ).order_by('-total_visits')[:8] # Get top 8 areas by summed visits
    
    trending_pages_data = []
    for area_obj in top_areas:
        trending_pages_data.append({
            'path': area_obj.name,
            'visits': area_obj.total_visits, # type: ignore
            'name': area_obj.name.title()
        })
    
    # Debug print (can be removed or kept for monitoring)
    logger.info(f"Found {len(trending_pages_data)} trending areas (aggregated)")
    for p in trending_pages_data:
        logger.info(f"Area: {p['name']}, Path: {p['path']}, Total Visits: {p['visits']}")
    
    # Get trending articles based on views, prioritizing recent articles
    one_week_ago = timezone.now() - timedelta(days=7)
    
    # First, try to get trending articles from the last week
    recent_trending = Article.objects.filter(
        created_at__gte=one_week_ago
    ).annotate(
        total_visits=Sum('urlmodel__visits')
    ).filter(
        total_visits__isnull=False,
        total_visits__gt=0
    ).order_by('-total_visits', '-created_at')[:6]
    
    # If we don't have enough recent trending articles, get the most viewed articles overall
    if len(recent_trending) < 6:
        # Get all articles with visits, excluding the ones we already have
        recent_trending_ids = [article.pk for article in recent_trending]
        
        additional_articles = Article.objects.annotate(
            total_visits=Sum('urlmodel__visits')
        ).filter(
            total_visits__isnull=False,
            total_visits__gt=0
        ).exclude(
            pk__in=recent_trending_ids
        ).order_by('-total_visits', '-created_at')[:6-len(recent_trending)]
        
        # Combine the lists
        trending_articles = list(recent_trending) + list(additional_articles)
    else:
        trending_articles = list(recent_trending)
    
    # If still no articles with visits, get the most recent articles
    if not trending_articles:
        trending_articles = list(Article.objects.all().order_by('-created_at')[:6])
    
    # Debug logging for trending articles
    logger.info(f"Found {len(trending_articles)} trending articles from the last week")
    for i, article in enumerate(trending_articles[:5], 1):  # Log first 5
        visits = getattr(article, 'total_visits', 0) or 0
        logger.info(f"  {i}. '{article.title[:50]}...' - {visits} visits")
    
    context = {
        'trending_pages': trending_pages_data,
        'trending_articles': trending_articles
    }
    return render(request, 'init.html', context)

genai.configure(api_key='AIzaSyDf2x-ENW14KrJEJZSIgY4LLnTv6ns52bQ')  # type: ignore

def autocomplete_area(request):
    if 'term' in request.GET:
        # Normalize the search term
        term = normalize_area_name(request.GET.get('term'))
        qs = Area.objects.filter(name__icontains=term)
        # Keep capitalization for display purposes if needed, but filtering is case-insensitive now
        area_names = list(set(area.name.title() for area in qs)) # Use title() for display
        return JsonResponse(area_names, safe=False)
    return JsonResponse([], safe=False)

def all_articles_view(request):
    articles = Article.objects.all().order_by('-created_at')
    
    context = {
        'articles': articles,
    }
    return render(request, 'all_articles.html', context)

def article_detail_by_slug(request, area_name, article_slug):
    # Normalize area name from URL
    normalized_area_name = normalize_area_name(area_name)
    area = get_object_or_404(Area, name=normalized_area_name)
    # Use the original area_name (or normalized) for context/display if needed
    # Keeping original for potential display differences, but using normalized for lookup
    article = get_object_or_404(Article, slug=article_slug, area=area)
    
    # Check if questions already exist for the article
    if not questions.objects.filter(article=article).exists():
        questions_data = generate_article_qs(article)
        for question in questions_data:
            questions.objects.create(
                question=question,
                article=article
            )

    context = {
        'article': article,
        'area': area,
        'questions': questions.objects.filter(article=article),
    }
    return render(request, 'article_detail.html', context)

# Keep the old view for backwards compatibility if needed
def article_detail(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    # Find the area associated with this article using the ForeignKey
    # The relationship is now direct: article.area
    area = article.area

    if area:
        # Redirect to the new URL pattern using the area's actual name
        return redirect('article_detail_by_slug', area_name=area.name, article_slug=article.slug)
    
    # If no area is found, fall back to the original view
    if not questions.objects.filter(article=article).exists():
        questions_data = generate_article_qs(article)
        for question in questions_data:
            questions.objects.create(
                question=question,
                article=article
            )

    context = {
        'article': article,
        'questions': questions.objects.filter(article=article),
    }
    return render(request, 'article_detail.html', context)


def post_create(request):
    if request.method == 'POST':
        # Normalize the area name from the form
        area_name = normalize_area_name(request.POST.get('area', ''))
        content = request.POST.get('content', '').strip()
        reporter_name = request.POST.get('reporter_name', '').strip()
        form = PostForm(request.POST) # Still pass original POST data to form
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            if not content:
                errors['content'] = True
            if not area_name: # Check normalized name
                errors['area'] = True

            if errors:
                 return JsonResponse({'success': False, 'errors': errors})

            # Since we normalized area_name, don't rely on form validation for it here
            # Just proceed with creating/getting the area
            area, _ = Area.objects.get_or_create(name=area_name)
            # Manually create post if content is valid
            if content:
                # Assign the Area object directly to the ForeignKey
                post = Post.objects.create(content=content, area=area, reporter_name=reporter_name)
                # No longer need area.posts.add(post) because the relationship is handled by the ForeignKey
                time.sleep(1) # Keep the delay if needed
                return JsonResponse({'success': True})
            else:
                # Should not happen if initial check passed, but as fallback
                return JsonResponse({'success': False, 'errors': {'content': True}})


        # Non-AJAX request handling (standard form submission)
        if form.is_valid():
            post = form.save(commit=False)
            post.content = content # Already got content above
            post.reporter_name = reporter_name
            # Get the Area object
            area, _ = Area.objects.get_or_create(name=area_name)
            # Assign the Area object directly to the ForeignKey
            post.area = area
            post.save() # Save the post with the associated area
            # No longer need area.posts.add(post)
            return redirect(f'/{area_name}/')
        else:
             # If form is invalid (e.g., other fields added later), render with errors
             # Pass the original potentially non-normalized area back to the form for display
             form = PostForm(initial={'area': request.POST.get('area', ''), 'content': content})
             return render(request, 'post_form.html', {'form': form})

    else: # GET request
        content = request.GET.get('content', '')
        # Normalize area from GET param if present
        area_param = normalize_area_name(request.GET.get('area', ''))
        form = PostForm(initial={'area': area_param, 'content': content})

    return render(request, 'post_form.html', {'form': form})

def categorize_advertisement(content, max_retries=3, retry_delay=2):
    """
    Categorize advertisement using Gemini API with retry logic.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            schema = {
                "type": "object",
                "properties": {
                    "category": {"type": "string"}
                },
                "required": ["category"]
            }

            model = genai.GenerativeModel(
                'gemini-2.0-flash',
                generation_config={"response_mime_type": "application/json",
                                   "response_schema": schema}
            )

            prompt = f"Categorize this advertisement into the most appropriate single category. Advertisement content: {content}"
            response = model.generate_content(prompt)
            parsed_data = json.loads(response.text)
            return parsed_data['category']
        except Exception as e:
            logger.exception(f"Error in categorize_advertisement (attempt {attempt+1}/{max_retries}): {e}")
            attempt += 1
            if attempt < max_retries:
                time.sleep(retry_delay)
    logger.error(f"categorize_advertisement failed after {max_retries} attempts.")
    return "general"

def advertisement_create(request):
    if request.method == 'POST':
        area_name = normalize_area_name(request.POST.get('area', ''))
        content = request.POST.get('content', '').strip()
        advertiser_name = request.POST.get('advertiser_name', '').strip()
        form = AdvertisementForm(request.POST, request.FILES)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            if not content:
                errors['content'] = True
            if not area_name:
                errors['area'] = True

            if errors:
                return JsonResponse({'success': False, 'errors': errors})

            area, _ = Area.objects.get_or_create(name=area_name)
            if content:
                # Categorize the advertisement
                category = categorize_advertisement(content)
                advertisement = Advertisement.objects.create(
                    content=content, 
                    area=area, 
                    advertiser_name=advertiser_name,
                    category=category,
                    image=request.FILES.get('image')
                )
                time.sleep(1)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': {'content': True}})

        # Non-AJAX request handling
        if form.is_valid():
            advertisement = form.save(commit=False)
            area, _ = Area.objects.get_or_create(name=area_name)
            advertisement.area = area
            # Categorize the advertisement
            advertisement.category = categorize_advertisement(content)
            advertisement.save()
            return redirect(f'/{area_name}/')
        else:
            return render(request, 'advertisement_form.html', {'form': form})

    else:  # GET request
        content = request.GET.get('content', '')
        area_param = normalize_area_name(request.GET.get('area', ''))
        form = AdvertisementForm(initial={'area': area_param, 'content': content})

    return render(request, 'advertisement_form.html', {'form': form})

def advertisements_by_category(request, area_name, category):
    normalized_area_name = normalize_area_name(area_name)
    area = get_object_or_404(Area, name=normalized_area_name)
    advertisements = Advertisement.objects.filter(area=area, category=category).order_by('-created_at')
    
    context = {
        'advertisements': advertisements,
        'area': area,
        'category': category.replace('-', ' ').title(),
        'category_slug': category
    }
    return render(request, 'advertisements_by_category.html', context)

def trending_articles(request):
    """
    API endpoint to return trending articles for the post form sidebar
    """
    # Get recent articles, limited to 5
    articles = Article.objects.all().order_by('-created_at')[:5]
    
    articles_data = []
    for article in articles:
        # Construct the URL for the article
        if article.area:
            article_url = f"/{article.area.name}/{article.slug}/"
        else:
            article_url = f"/article/{article.pk}/"
            
        articles_data.append({
            'title': article.title,
            'category': article.category,
            'created_at': article.created_at.isoformat(),
            'cover_image': article.cover_image,
            'url': article_url
        })
    
    return JsonResponse({'articles': articles_data})

@require_POST
def like_article(request, article_id):
    """
    API endpoint to like an article
    """
    try:
        article = get_object_or_404(Article, pk=article_id)
        article.likes += 1
        article.save()
        return JsonResponse({'success': True, 'likes': article.likes})
    except Exception as e:
        logger.exception(f"Error liking article {article_id}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def get_posts_content_by_area(area_name: str, since=None):
    """
    Fetches the posts for a given area.
    Optionally filters posts created after a specific timestamp ('since').
    """
    try:
        normalized_area = normalize_area_name(area_name)
        area = Area.objects.get(name=normalized_area)
        # Use the related name from Post.area ForeignKey
        posts_query = area.area_posts.all() # type: ignore
        if since:
            logger.info(f"Fetching posts for '{normalized_area}' created after {since}")
            posts_query = posts_query.filter(date_posted__gt=since)
        else:
            logger.info(f"Fetching all posts for '{normalized_area}' (initial generation or no 'since' date)")
        
        if not posts_query.exists():
            logger.info("No posts found matching the criteria.")
            return None # Return None if no posts match

        return posts_query

    except Area.DoesNotExist:
        logger.error(f"Area '{area_name}' not found.")
        return None
    except Exception as e:
        logger.exception(f"Error getting posts content for '{area_name}': {e}")
        return None


def generate_news(request):
    if request.method == 'POST':
        # Normalize the area name from the form
        area_name = normalize_area_name(request.POST.get('area'))
        if not area_name:
             messages.error(request, "Area name cannot be empty.")
             return redirect(request.META.get('HTTP_REFERER', '/')) # Redirect back

        try:
            # Use normalized name to get the Area
            area = Area.objects.get(name=area_name)
        except Area.DoesNotExist:
             messages.error(request, f"Area '{request.POST.get('area')}' not found.") # Show original input in message
             # Optionally create it here if desired:
             # area, _ = Area.objects.get_or_create(name=area_name)
             return redirect(request.META.get('HTTP_REFERER', '/'))

        logger.info(f"Generating news for area: {area_name}")
        last_gen_time = area.last_generated_at
        logger.info(f"Last generation time for {area_name}: {last_gen_time}")

        # Get content of NEW posts since the last generation
        new_posts = get_posts_content_by_area(area_name, since=last_gen_time)

        if not new_posts:
            logger.info(f"No new comments found for {area_name} since {last_gen_time}. No articles generated.")
            messages.info(request, f"No new comments found for '{area.name.title()}'. News is up to date.")
            return redirect(f'/{area_name}/') # Redirect to the area page

        # Construct comments string including reporter names
        comments_list = []
        for post in new_posts:
            if post.reporter_name:
                comments_list.append(f'"{post.content}" - {post.reporter_name}')
            else:
                comments_list.append(f'"{post.content}"')
        
        new_comments_text = " ".join(comments_list)


        logger.info(f"Found new comments for {area_name}. Sending to LLM...")
        # Generate articles ONLY from the new comments
        # Consider adjusting the run_gemini prompt if you want it to be aware
        # that these are *new* comments, e.g., ask it to generate updates or new topics.
        articles_data = run_gemini(new_comments_text, area_name)

        logger.info(f"LLM generated {len(articles_data)} new articles")

        if not articles_data:
             logger.warning("LLM did not return any articles after retries.")
             messages.warning(request, "Could not generate new articles from the latest comments. Please try again later.")
             # Do NOT update last_generated_at here, so the user can retry
             return redirect(f'/{area_name}/')

        newly_created_count = 0
        for article_data in articles_data:
            title = article_data.get('title')
            content = article_data.get('content')
            reporter_name = article_data.get('reporter_name')

            if not title or not content:
                logger.warning("Skipping article data with missing title or content.")
                continue

            # Fetch cover image using image keywords if available, otherwise use title
            category = article_data.get('category', 'news')
            image_keywords = article_data.get('image_keywords')
            # Use image keywords if available, otherwise fall back to title
            search_query = image_keywords if image_keywords else title
            logger.info(f"Using image search query: '{search_query}' (from keywords: {image_keywords is not None}) for article: '{title}'")
            cover_image_url = fetch_cover_image(search_query, category)

            try:
                article = Article.objects.create(
                    title=title,
                    content=content,
                    category=category,
                    cover_image=cover_image_url,
                    reporter_name=reporter_name,
                    # Assign the Area object directly during creation
                    area=area
                )
                # No longer need area.articles.add(article)
                newly_created_count += 1
                # Use article.pk instead of article.id to satisfy linter
                logger.info(f"Created article: {article.title} (PK: {article.pk}) for Area: {area.name}")
            except Exception as e:
                 logger.exception(f"Error creating article '{title}': {e}")

        if newly_created_count > 0:
            # Update the last generated timestamp for the area AFTER processing
            area.last_generated_at = timezone.now()
            area.save(update_fields=['last_generated_at'])
            logger.info(f"Updated last_generated_at for {area_name} to {area.last_generated_at}")

        messages.success(request, f"Successfully generated {newly_created_count} new articles for '{area.name.title()}'.")
        return redirect(f'/{area_name}/')

    # Handle GET request (optional, maybe redirect or show a form)
    return redirect('/') # Or wherever appropriate for a GET request

def fetch_external_news_via_rss(area_name, max_results=10):
    """Get news from Google News RSS feed directly, with caching."""
    # Normalize area_name for cache key consistency
    normalized_area_name_for_cache = normalize_area_name(area_name)
    cache_key = f"external_news_rss_{urllib.parse.quote(normalized_area_name_for_cache)}_{max_results}"
    cached_articles = cache.get(cache_key)

    if cached_articles is not None: # Check for None explicitly, as an empty list is a valid cached result
        logger.info(f"Returning cached RSS news for '{area_name}' (normalized: '{normalized_area_name_for_cache}', max_results={max_results})")
        return cached_articles

    logger.info(f"No cache hit for RSS news: '{area_name}' (normalized: '{normalized_area_name_for_cache}'). Fetching from source.")
    articles_to_cache = [] # Initialize with an empty list
    try:
        # Use normalized_area_name_for_cache for the query as well for consistency
        query = urllib.parse.quote(f"{normalized_area_name_for_cache} news") 
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        logger.info(f"Trying Google News RSS feed for: {normalized_area_name_for_cache} with URL: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            logger.info(f"No entries found in RSS feed for '{normalized_area_name_for_cache}'. Trying broader query.")
            query_broader = urllib.parse.quote(normalized_area_name_for_cache) 
            rss_url_broader = f"https://news.google.com/rss/search?q={query_broader}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(rss_url_broader)
            if feed.entries:
                logger.info(f"Found entries with broader query for '{normalized_area_name_for_cache}'.")
            else:
                logger.info(f"Still no entries found with broader RSS query for '{normalized_area_name_for_cache}'.")

        for entry in feed.entries[:max_results]:
            content = entry.get('summary', '')
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.get_text()
            
            image_url = fetch_cover_image(entry.get('title', ''))
            
            published_time = timezone.now() 
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    published_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                except Exception as e_date:
                    logger.exception(f"Could not parse date for article '{entry.get('title')}': {e_date}")
            elif hasattr(entry, 'published') and entry.published:
                 try:
                    dt = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
                    published_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                 except ValueError:
                     try:
                         dt = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
                         published_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                     except ValueError as e_date_str:
                         logger.exception(f"Could not parse string date '{entry.published}' for article '{entry.get('title')}': {e_date_str}")

            article_data = {
                'title': entry.get('title', ''),
                'content': content,
                'cover_image': image_url,
                'created_at': published_time,
                'category': 'Google News',
                'is_external': True,
                'external_url': entry.get('link', '#'),
            }
            articles_to_cache.append(article_data)
        
        logger.info(f"Found {len(articles_to_cache)} articles via Google News RSS for '{normalized_area_name_for_cache}'")
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, articles_to_cache, timeout=3600)
        return articles_to_cache
    except Exception as e:
        logger.exception(f"RSS feed error for {area_name} (normalized: {normalized_area_name_for_cache}): {e}")
        import traceback
        traceback.print_exc()
        # Cache an empty list for a shorter period (e.g., 15 mins) on error to avoid hammering
        cache.set(cache_key, [], timeout=900) 
        return []

# This function now solely relies on the RSS feed method.
def get_google_news_for_area(area_name, max_results=10):
    """
    Fetch news articles for the area, using Google News RSS as the source.
    """
    logger.info(f"Fetching external news for '{area_name}' using RSS feed.")
    articles = fetch_external_news_via_rss(area_name, max_results)
    if not articles:
        logger.info(f"No articles found for '{area_name}' from any external source.")
    return articles

def articles_by_area(request, area_name):
    # Normalize area name from URL
    normalized_area_name = normalize_area_name(area_name)
    area = get_object_or_404(Area, name=normalized_area_name)
    
    # Get articles for this area using the reverse relationship
    articles = list(area.articles.all().order_by('-created_at')) # type: ignore
    
    # If no articles found, fetch from Google News
    if not articles:
        google_news_articles = get_google_news_for_area(area_name)
        # Only use Google News if we found results
        if google_news_articles:
            articles = google_news_articles
    
    # Get advertisements for this area and group by category
    advertisements = Advertisement.objects.filter(area=area).order_by('-created_at')
    ad_categories = {}
    for ad in advertisements:
        if ad.category not in ad_categories:
            ad_categories[ad.category] = []
        ad_categories[ad.category].append(ad)
    
    # Convert ad_categories.items() to a list for template usage
    ad_categories_list = list(ad_categories.items())
    
    # Check if this was an auto-corrected search or suggestion
    auto_corrected = request.session.pop('auto_corrected', False)
    suggestion_only = request.session.pop('suggestion_only', False)
    original_query = request.session.pop('original_query', None)
    corrected_query = request.session.pop('corrected_query', None)
    
    # Check if we're showing Google News (handle articles attribute safely)
    has_local_articles = False
    try:
        has_local_articles = area.articles.exists() # type: ignore
    except Exception:
        # If there's no articles relation, consider it has no articles
        has_local_articles = False
    
    context = {
        'area': area,
        'articles': articles,
        'ad_categories': ad_categories,
        'ad_categories_list': ad_categories_list,
        'auto_corrected': auto_corrected,
        'suggestion_only': suggestion_only,
        'original_query': original_query,
        'corrected_query': corrected_query,
        'showing_google_news': not has_local_articles and bool(articles),
    }
    return render(request, 'news.html', context)


def article_detail_view(request, article_id):
    # Retrieve the article by its ID or return a 404 error if not found
    article = get_object_or_404(Article, id=article_id)
    
    context = {
        'article': article,
    }
    return render(request, 'article_detail.html', context)

def trending_articles(request):
    """
    API endpoint to return trending articles for the post form sidebar
    """
    # Get recent articles, limited to 5
    articles = Article.objects.all().order_by('-created_at')[:5]
    
    # Format the articles as JSON
    articles_data = []
    for article in articles:
        article_data = {
            'title': article.title,
            'category': article.category,
            'created_at': article.created_at.isoformat(),
            'url': f'/article/{article.pk}/' if article.pk else '#',
            'cover_image': article.cover_image,
        }
        if article.slug and article.area:
            article_data['url'] = f'/{article.area.name}/{article.slug}/'
        
        articles_data.append(article_data)
    
    return JsonResponse({'articles': articles_data})

# --------------------
# AJAX Like Endpoint
# --------------------

@require_POST
def like_article(request, article_id):
    """Increment the like count for an article (AJAX)."""
    article = get_object_or_404(Article, pk=article_id)
    # Atomic update to avoid race conditions
    Article.objects.filter(pk=article_id).update(likes=F('likes') + 1)
    # Refresh from the database to get the updated value
    article.refresh_from_db(fields=['likes'])
    return JsonResponse({'success': True, 'likes': article.likes})
