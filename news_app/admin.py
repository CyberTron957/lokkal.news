from django.contrib import admin
from .models import Post,Article,URLModel, Area

admin.site.register(Post)
admin.site.register(Article)
admin.site.register(URLModel)
admin.site.register(Area)

# Register your models here.
