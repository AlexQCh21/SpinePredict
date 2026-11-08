from django.conf import settings


def demo(request):
    return {
        'DEMO_MODE': getattr(settings, 'DEMO_MODE', False),
        'DEMO_CLEANUP_INTERVAL_SECONDS': getattr(settings, 'DEMO_CLEANUP_INTERVAL_SECONDS', 3600),
        'DEMO_ADMIN_USERNAME': getattr(settings, 'DEMO_ADMIN_USERNAME', 'demo_admin'),
        'DEMO_SPECIALIST_USERNAME': getattr(settings, 'DEMO_SPECIALIST_USERNAME', 'demo_especialista'),
    }
