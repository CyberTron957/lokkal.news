from django.contrib import admin
from .models import Post,Article,URLModel

admin.site.register(Post)
admin.site.register(Article)
admin.site.register(URLModel)

# Register your models here.
