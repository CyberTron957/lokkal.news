from datetime import date
from unicodedata import category
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import hashlib



class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=100, default="news")
    cover_image = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    likes = models.PositiveIntegerField(default=0)
    area = models.ForeignKey('Area', on_delete=models.CASCADE, related_name='articles', null=True, blank=True)
    reporter_name = models.CharField(max_length=100, blank=True, null=True, help_text="Displayed under the article title. Can be a name or a generic credit like 'Community Reports'.")

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
    area = models.ForeignKey('Area', on_delete=models.CASCADE, related_name='area_posts')
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    reporter_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Post in {self.area.name}: {self.content[:50]}..." if self.area else f"Post (PK:{self.pk}): {self.content[:50]}..."

class URLModel(models.Model):
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    visits = models.IntegerField(default=0)
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.ForeignKey('Area', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.path



class Advertisement(models.Model):
    content = models.TextField()
    category = models.CharField(max_length=100, default="general")
    created_at = models.DateTimeField(auto_now_add=True)
    area = models.ForeignKey('Area', on_delete=models.CASCADE, related_name='advertisements', null=True, blank=True)
    advertiser_name = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='advertisements/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            import time
            unique_hash = hashlib.sha256(f"{self.content[:50]}{time.time()}".encode()).hexdigest()[:8]
            self.slug = f"ad-{unique_hash}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ad: {self.content[:50]}..." if len(self.content) > 50 else f"Ad: {self.content}"

    class Meta:
        ordering = ['-created_at']

class Area(models.Model):
    name = models.CharField(max_length=255, unique=True)
    last_generated_at = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name