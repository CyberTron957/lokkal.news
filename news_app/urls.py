from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_and_generate, name='upload_and_generate'),
    path('news/', views.news_view, name='news_view'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),  # New URL for article details

]
