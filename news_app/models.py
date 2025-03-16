from datetime import date
from unicodedata import category
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import hashlib



class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.TextField(default="news")
    cover_image = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_hash = hashlib.sha256(self.title.encode()).hexdigest()  # Generate a unique hash
            self.slug = f"{slugify(self.title)}-{unique_hash}"  # Append the hash to the slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']  # Add default ordering

class questions(models.Model):
    question = models.CharField(max_length=255)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return self.question
    
class Post(models.Model):
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    area = models.CharField(max_length=255)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)  

    def save(self, *args, **kwargs):
        self.area = self.area.lower()  # Convert to lowercase
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)  # type: ignore

class URLModel(models.Model):
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    visits = models.IntegerField(default=0)
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey('Area', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.path



class Area(models.Model):
    name = models.CharField(max_length=255)
    articles = models.ManyToManyField(Article, related_name='areas')
    posts = models.ManyToManyField(Post, related_name='areas')

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name