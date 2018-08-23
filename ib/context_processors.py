from django.contrib.sites.shortcuts import get_current_site


def website(request):
    """
    Return website name.
    """
    return {'website': get_current_site(request)}
