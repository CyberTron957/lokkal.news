import re
from .models import URLModel, Area, Article
class PageViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only track GET requests
        if request.method == 'GET':
            path = request.path.strip('/')
            
            if path:
                parts = path.split('/')
                
                # Handle area visits (like /sanfrancisco/)
                if len(parts) == 1:
                    area_name = parts[0].lower()
                    try:
                        area = Area.objects.get(name=area_name)
                        # Check if a URLModel already exists for this area
                        if URLModel.objects.filter(area=area).exists():
                            url_obj, created = URLModel.objects.get_or_create(path=path)
                            url_obj.area = area
                            url_obj.article = None  # Ensure it's not an article
                            url_obj.visits += 1
                            url_obj.save()
                    except Area.DoesNotExist:
                        pass
                # Handle area/article-slug visits (like /sanfrancisco/local-news-title)
                elif len(parts) == 2:
                    area_name = parts[0].lower()
                    article_slug = parts[1]
                    
                    try:
                        area = Area.objects.get(name=area_name)
                        article = Article.objects.get(slug=article_slug, areas=area)
                        
                        url_obj, created = URLModel.objects.get_or_create(path=path)
                        url_obj.article = article
                        url_obj.area = area
                        url_obj.visits += 1
                        url_obj.save()
                    except (Area.DoesNotExist, Article.DoesNotExist):
                        pass
                        
        return response