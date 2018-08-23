from django.urls import re_path, include
from page.views import MenuRedirectView, repertory_demarcation, repertory_kwarg, MenuDetailView
from publication.urls import urlpatterns as _urlpatterns

app_name = 'page'

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    re_path(r'^(?P<' + repertory_kwarg + '>[a-z0-9-' + repertory_demarcation + ']+)/', include(_urlpatterns)),
    re_path(r'^(?P<' + repertory_kwarg + '>[a-z0-9-' + repertory_demarcation + ']+)/',
            MenuRedirectView.as_view(), name='menu-detail'),
]
