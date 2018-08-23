from django.contrib.sites.shortcuts import get_current_site
from django.views.generic.dates import ArchiveIndexView, MonthArchiveView, YearArchiveView, WeekArchiveView
from django.views.generic.base import View
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.views import redirect_to_login
from publication.models import Entry, FlatPage
from page.views import repertory_kwarg, MenuDetailView


class EntryMixinView(object):
    model = Entry
    date_field = 'created'
    paginate_by = 10
    make_object_list = True
    allow_empty = False

    def get(self, request, *args, **kwargs):
        directory = kwargs.get(repertory_kwarg)
        _kwargs = {repertory_kwarg: directory}
        self.menu_context = MenuDetailView.as_view()(request, **_kwargs)

        return super(EntryMixinView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(EntryMixinView, self).get_queryset()
        return queryset.filter(menu=self.menu_context['page_menu_object']).select_related('user')

    def get_dated_items(self):
        triple = super(EntryMixinView, self).get_dated_items()
        triple[2].update(self.menu_context)

        return triple[0], triple[1], triple[2]


class EntryArchiveView(EntryMixinView, ArchiveIndexView):
    pass


class EntryYearArchiveView(EntryMixinView, YearArchiveView):
    pass


class EntryMonthArchiveView(EntryMixinView, MonthArchiveView):
    month_format = "%m"


class EntryWeekArchiveView(EntryMixinView, WeekArchiveView):
    week_format = "%W"


class FlatPageView(View):
    model = FlatPage

    def get(self, request, *args, **kwargs):
        super(FlatPageView, self).get(request, *args, **kwargs)

        self.object = self.get_object(self.get_queryset())

        if self.object.registration_required and not request.user.is_authenticated:
            return redirect_to_login(request.path)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_queryset(self):
        queryset = super(FlatPageView, self).get_queryset()
        site_id = get_current_site(self.request).id
        return queryset.filter(sites=site_id)
