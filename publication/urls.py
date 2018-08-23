from django.urls import path, include
from publication.views import EntryMonthArchiveView, EntryYearArchiveView, EntryArchiveView, EntryWeekArchiveView

app_name = "publication"

publication_patterns = [
    path(
        '<int:year>/<int:month>/',
        EntryMonthArchiveView.as_view(),
        name="entry-month"
    ),
    path(
        '<int:year>/',
        EntryYearArchiveView.as_view(),
        name="entry-year"
    ),
    path('<int:year>/week/<int:week>/',
         EntryWeekArchiveView.as_view(),
         name="entry-week"),
    path(
        '',
        EntryArchiveView.as_view(),
        name="entry"
    ),
]

#flatpage_patterns = [
#    url(r'', FlatPageView.as_view(), name="flatpage")
#]

urlpatterns = [
    path('publications/', include((publication_patterns, 'publication'))),
    # url(r'flatpage/', include(flatpage_patterns))
]