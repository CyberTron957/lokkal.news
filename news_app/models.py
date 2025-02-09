from datetime import date
from django.db import models
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    cover_image = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pincode = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class questions(models.Model):
    question = models.CharField(max_length=255)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return self.question
    
class Post(models.Model):
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    pincode = models.CharField(max_length=255)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)  

    def __str__(self):
        return str(self.id) # type: ignore

class URLModel(models.Model):
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    visits = models.IntegerField(default=0)
    is_article = models.BooleanField(default=False)

    def __str__(self):
        return self.path
