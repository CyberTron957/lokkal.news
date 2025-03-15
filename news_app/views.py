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

def display_text_file(request):
    file_path = os.path.join('news_app/static/news_app/files/16667B0129E33E0CDEA4DAC33EE2E3D7.txt')  # Update with your file path
    with open(file_path, 'r') as file:
        content = file.read()
    return HttpResponse(content, content_type='text/plain')

genai.configure(api_key='AIzaSyDf2x-ENW14KrJEJZSIgY4LLnTv6ns52bQ')

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
            'gemini-1.5-pro',
            generation_config={"response_mime_type": "application/json",
                               "response_schema": schema}
        )

        response = model.generate_content(f"Based on the diverse comments collected from individuals in my area, please create a series of engaging news articles that effectively group similar topics and themes. Here are the comments: {text}")
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

        response = model.generate_content(f"As an AI tasked with enhancing community engagement, please generate 3  insightful short questions based on the following article. These questions should encourage readers to share their own experiences or provide additional comments that could enrich the article: Title: {article.title}. Content: {article.content}")
        parsed_data = json.loads(response.text)
        return parsed_data['questions']
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_cover_image(query):
    try:
        url = f"https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "client_id":"LSOUqV2JJVVQMYMapOqQdsMKkC1_Nrmu0w45m5NHpQc",
            "per_page": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["results"]:
            return data["results"][0]["urls"]["regular"]  # Get the URL of the first image
    except Exception as e:
        print(f"Error fetching image: {e}")
    return None


def upload_and_generate(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_path = default_storage.save('uploads/' + file.name, file)
        with open(file_path, 'r') as f:
            text = f.read()

        # Generate articles
        articles = run_gemini(text)

        # Save articles to the database with cover images
        for article_data in articles:
            cover_image_url = fetch_cover_image(article_data['title'] or article_data['content'])
            Article.objects.create(
                title=article_data['title'],
                content=article_data['content'],
                cover_image=cover_image_url
            )

        return redirect('news_view')

    return render(request, 'upload.html')

def init_view(request):
    if request.method == 'POST':
        area_name = request.POST.get('area').lower()
        area, _ = Area.objects.get_or_create(name=area_name)
        return redirect(f'/area/{area_name}/')
   
    # Get area pages with the most visits
    area_pages = URLModel.objects.filter(
        path__startswith='area/',  # Focus on area pages only
        area__isnull=False  # Make sure area is connected
    ).order_by('-visits')[:8]  # Get the top 8 most visited
    
    trending_pages = []
    for page in area_pages:
        # Extract area name from the path
        area_name = page.path.split('/')[1] if len(page.path.split('/')) > 1 else None
        if area_name:
            # Set display name for the template
            page.display_name = area_name.title()  # Capitalize for nicer display
            trending_pages.append(page)
    
    # Debug info
    print(f"Found {len(trending_pages)} trending areas")
    for p in trending_pages:
        print(f"Area: {p.display_name}, Path: {p.path}, Visits: {p.visits}")
    
    # Get trending articles
    trending_articles = URLModel.objects.filter(is_article=True).order_by('-visits')[:10]
    trending_article_ids = [int(article.path.split('/')[1]) for article in trending_articles]
    trending_articles = Article.objects.filter(id__in=trending_article_ids)

    context = {
        'trending_pages': trending_pages,
        'trending_articles': trending_articles
    }
    return render(request, 'init.html', context)

def autocomplete_area(request):
    if 'term' in request.GET:
        qs = Area.objects.filter(name__icontains=request.GET.get('term'))
        area_names = list(set(area_name.capitalize() for area_name in qs.values_list('name', flat=True)))
        return JsonResponse(area_names, safe=False)
    return JsonResponse([], safe=False)

def news_view(request):
    articles = Article.objects.all()
    return render(request, 'news.html', {'articles': articles})


def article_detail(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    previous_url = request.META.get('HTTP_REFERER', 'news_view')
    
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
        'questions': questions.objects.filter(article=article),
        'previous_url': previous_url
    }
    return render(request, 'article_detail.html', context)




def post_create(request):
    if request.method == 'POST':
        area_name = request.POST.get('area', '').lower()
        content = request.POST.get('content', '').strip()
        form = PostForm(request.POST)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if not content or not area_name:
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'content': not content,
                        'area': not area_name
                    }
                })
            
            if form.is_valid():
                post = form.save(commit=False)
                post.content = content
                area, _ = Area.objects.get_or_create(name=area_name)
                post.save()
                area.posts.add(post)
                
                time.sleep(1)
                return JsonResponse({'success': True})
            
            return JsonResponse({'success': False, 'errors': form.errors})
        
        if form.is_valid():
            post = form.save(commit=False)
            post.content = content
            area, _ = Area.objects.get_or_create(name=area_name)
            post.save()
            area.posts.add(post)
            return redirect(f'/area/{area_name}/')
    else:
        content = request.GET.get('content', '')
        area = request.GET.get('area', '')
        form = PostForm(initial={'area': area, 'content': content})
    
    return render(request, 'post_form.html', {'form': form})


def get_posts_content_by_area(area_name):
    area = Area.objects.get(name=area_name)
    posts = area.posts.all()
    all_content = '" "'.join(post.content for post in posts)
    return all_content



def generate_news(request):
    if request.method == 'POST':
        area_name = request.POST.get('area').lower()
        area, _ = Area.objects.get_or_create(name=area_name)
        
        print(f"Generating news for area: {area_name}")
        
        # Get existing articles for this area
        existing_articles = area.articles.all()
        if existing_articles.exists():
            print(f"Removing {existing_articles.count()} existing articles")
            area.articles.clear()
        
        comments = get_posts_content_by_area(area_name)
        articles = run_gemini(comments)
        
        print(f"Generated {len(articles)} new articles")
        
        for article_data in articles:
            cover_image_url = fetch_cover_image(article_data['title'] or article_data['content'])
            article = Article.objects.create(
                title=article_data['title'],
                content=article_data['content'],
                category=article_data.get('category', 'news'),
                cover_image=cover_image_url
            )
            # Explicitly add the article to the area
            area.articles.add(article)
            print(f"Created and associated article: {article.title}")
        
        # Verify the association
        print(f"Total articles now associated with {area_name}: {area.articles.count()}")
        
        return redirect(f'/area/{area_name}/')
    
def articles_by_area(request, area_name):
    area = get_object_or_404(Area, name=area_name.lower())
    
    # Get all articles
    all_articles = Article.objects.all()
    print(f"Total articles in database: {all_articles.count()}")
    
    # Get articles for this area
    articles = area.articles.all().order_by('-created_at')
    print(f"Area: {area}")
    print(f"Number of articles for this area: {articles.count()}")
    
    if articles.exists():
        print(f"First article title: {articles.first().title}")
    
    context = {
        'area': area,
        'articles': articles,
    }
    return render(request, 'news.html', context)