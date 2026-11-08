from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


def bad_request(request, exception=None):
    return render(request, '400.html', status=400)


def permission_denied(request, exception=None):
    return render(request, '403.html', status=403)


def page_not_found(request, exception=None):
    return render(request, '404.html', status=404)


@requires_csrf_token
def server_error(request):
    return render(request, '500.html', status=500)


@requires_csrf_token
def csrf_failure(request, reason=''):
    return render(request, '403_csrf.html', {'reason': reason}, status=403)
