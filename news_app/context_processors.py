from django.conf import settings

def google_analytics(request):
    """
    Add Google Analytics ID to the context if debug mode is off.
    This ensures analytics is only active in production, not during development.
    """
    if settings.DEBUG:
        # Return None during development/testing
        return {'GOOGLE_ANALYTICS_ID': None}
    return {'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID} 