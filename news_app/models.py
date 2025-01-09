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
    #title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    #author = models.ForeignKey(User, on_delete=models.CASCADE)
    pincode = models.CharField(max_length=255)


    def __str__(self):
        return str(self.id)
