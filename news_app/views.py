import time
from .forms import PostForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from .models import Article,Post,questions
from django.conf import settings
import google.generativeai as genai
import requests
import json
from django.http import JsonResponse

genai.configure(api_key='YOUR_API_KEY')

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
                            "content": {"type": "string"}
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

        response = model.generate_content(f"As an AI tasked with enhancing community engagement, please generate 3 insightful short questions based on the following article. These questions should encourage readers to share their own experiences or provide additional comments that could enrich the article: Title: {article.title}. Content: {article.content}")
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
            "client_id":"YOUR_CLIENT_ID",
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
        pincode = request.POST.get('pincode').lower()

        return redirect(f'/{pincode}/')

    return render(request,'init.html')


def autocomplete_pincode(request):
    if 'term' in request.GET:
        qs = Article.objects.filter(pincode__icontains=request.GET.get('term'))
        pincode = list(set(pin.capitalize() for pin in qs.values_list('pincode', flat=True)))
        return JsonResponse(pincode, safe=False)
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
        pincode = request.POST.get('pincode').lower()  # Save pincode in lower case

        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.content = request.POST.get('content')

            #post.author = request.user
            post.save()
            messages.success(request, 'Your post has been made!')
            return redirect(f'/{pincode}/')
    else:
        content = request.GET.get('content', '')
        pincode = request.GET.get('pincode', '')
        form = PostForm(initial={'pincode': pincode, 'content': content})
    return render(request, 'post_form.html', {'form': form})


def get_posts_content_by_pincode(pincode):

    posts = Post.objects.filter(pincode=pincode)
    all_content = '" "'.join(post.content for post in posts)

    return all_content



def generate_news(request):
    if request.method == 'POST':
        pincode = request.POST.get('pincode')

        # Remove existing articles for the pincode
        Article.objects.filter(pincode=pincode).delete()

        comments = get_posts_content_by_pincode(pincode)
        articles = run_gemini(comments)

        for article_data in articles:
            cover_image_url = fetch_cover_image(article_data['title'] or article_data['content'])
            Article.objects.create(
                title=article_data['title'],
                content=article_data['content'],
                cover_image=cover_image_url,
                pincode=pincode
            )
        return redirect(f'/{pincode}/')

def articles_by_pincode(request, pincode):
    articles = Article.objects.filter(pincode=pincode)
    context = {
        'pincode': pincode,
        'articles': articles,
    }
    return render(request, 'news.html', context)
