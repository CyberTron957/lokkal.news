from django.urls import path
from . import views

urlpatterns = [
    path('', views.init_view, name = 'enter_area'),
    path('upload/', views.upload_and_generate, name='upload_and_generate'),
    path('post/new/', views.post_create, name='post-create'),
    path('generate-news/', views.generate_news, name='generate_news'), # type: ignore
    path('autocomplete/area/', views.autocomplete_area, name='autocomplete_area'),
    path('all-articles/', views.all_articles_view, name='all-articles-view'),
    path('article/<int:article_id>/', views.article_detail_view, name='article_detail_by_id'),
    path('<str:area_name>/', views.articles_by_area, name='articles_by_area'),
    # Updated URL pattern for article details within an area
    path('<str:area_name>/<slug:article_slug>/', views.article_detail_by_slug, name='article_detail_by_slug'),
    # Keep this as the last pattern since it's more generic
]