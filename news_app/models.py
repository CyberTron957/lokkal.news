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

class Post(models.Model):
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    pincode = models.CharField(max_length=255)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)  

    def __str__(self):
        return str(self.id) # type: ignore
