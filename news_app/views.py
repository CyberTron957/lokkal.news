import time
from unicodedata import category
from .forms import PostForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from .models import Article, Post, questions, URLModel, Area
from django.conf import settings
import google.generativeai as genai
import requests
import json
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.urls import resolve
from django.utils import timezone
from datetime import timedelta
from django.template import loader
import os
import re # Import regular expressions for cleaning

# A simple list of common English stop words. You could expand this.
STOP_WORDS = set([
    "a", "an", "and", "are", "as", "at", "be", "but", "by",
    "for", "if", "in", "into", "is", "it",
    "no", "not", "of", "on", "or", "such",
    "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with", "over", "post-oc" # Added 'over' and 'post-oc' based on example
])

def normalize_area_name(name):
    """Converts to lowercase, strips whitespace, and collapses internal spaces."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name) # Replace multiple spaces with single space
    return name

def run_gemini(text):
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
                            "category": {"type": "string"}
                        },
                        "required": ["title", "content"]
                    }
                }
            },
            "required": ["articles"]
        }

        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={"response_mime_type": "application/json",
                               "response_schema": schema}
        )

        response = model.generate_content(f"Based on the diverse comments collected from individuals in my area, please create a series of long engaging news articles that effectively group similar topics and themes. Here are the comments: {text}")
        parsed_data = json.loads(response.text)
        return parsed_data['articles']
    except Exception as e:
        print(f"Error: {e}")
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

        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json",
                               "response_schema": schema}
        )

        response = model.generate_content(f"As an AI tasked with enhancing community engagement, please generate 3  insightful very short questions based on the following article. These questions should encourage readers to share their own experiences or provide additional comments that could enrich the article: Title: {article.title}. Content: {article.content}")
        parsed_data = json.loads(response.text)
        return parsed_data['questions']
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_cover_image(query, category=None):
    """
    Fetches a cover image from Unsplash based on a query and optional category.
    Filters stop words from the query for better relevance.
    """
    if not query:
        print("Error: Empty query passed to fetch_cover_image.")
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
         print(f"No significant keywords found in '{query}'. Falling back to: '{simplified_query}'")
    else:
        simplified_query = " ".join(keywords)
        print(f"Original query: '{query}', Category: '{category}', Keywords for search: '{simplified_query}'")

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
                print(f"  Successfully fetched image: {image_url}")
                return image_url
            else:
                print("  No regular URL found in the first image result.")
        else:
            print(f"  No image results found for query: '{simplified_query}'")
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching image from Unsplash: {e}")
    except Exception as e:
        print(f"  An unexpected error occurred: {e}")

    return None # Return None if anything goes wrong or no image is found


def init_view(request):
    if request.method == 'POST':
        # Normalize the area name from the form
        area_name = normalize_area_name(request.POST.get('area'))
        if not area_name:
            messages.error(request, "Area name cannot be empty.")
            return redirect('enter_area') # Redirect back to the init page
        area, _ = Area.objects.get_or_create(name=area_name)
        return redirect(f'/{area_name}/')
   
    # Get the most visited area pages
    area_urls = URLModel.objects.filter(
        area__isnull=False,  # Only get URLs associated with an area
        article__isnull=True  # Exclude article URLs
    ).order_by('-visits')[:8]
    
    trending_pages_data = []
    for url in area_urls:
        if url.area:
            trending_pages_data.append({
                'path': url.path,
                'visits': url.visits,
                'name': url.area.name.title()
            })
    
    # Debug print
    print(f"Found {len(trending_pages_data)} trending areas")
    for p in trending_pages_data:
        print(f"Area: {p['name']}, Path: {p['path']}, Visits: {p['visits']}")
    
    # Get trending articles - filter by article being not null
    trending_url_models = URLModel.objects.filter(
        article__isnull=False  # Must have an associated article
    ).order_by('-visits')[:10]
    
    # Extract the article objects directly
    trending_articles = []
    for url_model in trending_url_models:
        if url_model.article and url_model.article not in trending_articles:
            trending_articles.append(url_model.article)
            
    # Sort the trending articles by creation date (newest first)
    trending_articles.sort(key=lambda article: article.created_at, reverse=True)
    
    context = {
        'trending_pages': trending_pages_data,
        'trending_articles': trending_articles
    }
    return render(request, 'init.html', context)
genai.configure(api_key='AIzaSyDf2x-ENW14KrJEJZSIgY4LLnTv6ns52bQ') 

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
    article = get_object_or_404(Article, slug=article_slug, areas=area)
    
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
    # Find the first area associated with this article
    area = article.areas.first() # type: ignore
    
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
                post = Post.objects.create(content=content, area=area)
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


def get_posts_content_by_area(area_name, since=None):
    """
    Fetches the combined content of posts for a given area.
    Optionally filters posts created after a specific timestamp ('since').
    """
    try:
        area = Area.objects.get(name=area_name.lower()) # Keep lower() here for lookup if URLs/inputs aren't normalized
        # Use the related name from Post.area ForeignKey
        posts_query = area.area_posts.all() # type: ignore
        if since:
            print(f"Fetching posts for '{area_name}' created after {since}")
            posts_query = posts_query.filter(date_posted__gt=since)
        else:
            print(f"Fetching all posts for '{area_name}' (initial generation or no 'since' date)")

        posts = posts_query.order_by('date_posted') # Ensure order if needed by LLM

        if not posts.exists():
            print("No posts found matching the criteria.")
            return None # Return None if no posts match

        all_content = '" "'.join(post.content for post in posts)
        print(f"Found {posts.count()} posts, combined content length: {len(all_content)}")
        return all_content
    except Area.DoesNotExist:
        print(f"Area '{area_name}' not found.")
        return None
    except Exception as e:
        print(f"Error getting posts content for '{area_name}': {e}")
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

        print(f"Generating news for area: {area_name}")
        last_gen_time = area.last_generated_at
        print(f"Last generation time for {area_name}: {last_gen_time}")

        # Get content of NEW posts since the last generation
        new_comments = get_posts_content_by_area(area_name, since=last_gen_time)

        if not new_comments:
            print(f"No new comments found for {area_name} since {last_gen_time}. No articles generated.")
            messages.info(request, f"No new comments found for '{area.name.title()}'. News is up to date.")
            return redirect(f'/{area_name}/') # Redirect to the area page

        print(f"Found new comments for {area_name}. Sending to LLM...")
        # Generate articles ONLY from the new comments
        # Consider adjusting the run_gemini prompt if you want it to be aware
        # that these are *new* comments, e.g., ask it to generate updates or new topics.
        articles_data = run_gemini(new_comments)

        print(f"LLM generated {len(articles_data)} new articles")

        if not articles_data:
             print("LLM did not return any articles.")
             messages.warning(request, "Could not generate new articles from the latest comments.")
             # Update timestamp even if no articles generated to avoid reprocessing same comments
             area.last_generated_at = timezone.now()
             area.save(update_fields=['last_generated_at'])
             return redirect(f'/{area_name}/')

        newly_created_count = 0
        for article_data in articles_data:
            title = article_data.get('title')
            content = article_data.get('content')

            if not title or not content:
                print("Skipping article data with missing title or content.")
                continue

            # Fetch cover image using the refined logic (pass category too)
            category = article_data.get('category', 'news')
            cover_image_url = fetch_cover_image(title, category)

            try:
                article = Article.objects.create(
                    title=title,
                    content=content,
                    category=category,
                    cover_image=cover_image_url
                )
                # Associate the new article with the area
                area.articles.add(article)
                newly_created_count += 1
                print(f"Created and associated article: {article.title} (ID: {article.id})")
            except Exception as e:
                 print(f"Error creating or associating article '{title}': {e}")

        if newly_created_count > 0:
            # Update the last generated timestamp for the area AFTER processing
            area.last_generated_at = timezone.now()
            area.save(update_fields=['last_generated_at'])
            print(f"Updated last_generated_at for {area_name} to {area.last_generated_at}")

        messages.success(request, f"Successfully generated {newly_created_count} new articles for '{area.name.title()}'.")
        return redirect(f'/{area_name}/')

    # Handle GET request (optional, maybe redirect or show a form)
    return redirect('/') # Or wherever appropriate for a GET request

def articles_by_area(request, area_name):
    # Normalize area name from URL
    normalized_area_name = normalize_area_name(area_name)
    area = get_object_or_404(Area, name=normalized_area_name)
    
    # Get articles for this area
    articles = area.articles.all().order_by('-created_at')
    
    context = {
        'area': area,
        'articles': articles,
    }
    return render(request, 'news.html', context)


def article_detail_view(request, article_id):
    # Retrieve the article by its ID or return a 404 error if not found
    article = get_object_or_404(Article, id=article_id)
    
    context = {
        'article': article,
    }
    return render(request, 'article_detail.html', context)
