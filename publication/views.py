from django.views.generic.dates import ArchiveIndexView, MonthArchiveView, YearArchiveView, WeekArchiveView
from django.views.generic.list import ListView
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.utils.translation import gettext as _

from publication.models import Entry, FlatPage
from page.views import repertory_kwarg, MenuDetailView


class EntryMixinView(object):
    model = Entry
    date_field = 'created'
    paginate_by = 10
    make_object_list = True
    allow_empty = False

    def get(self, request, *args, **kwargs):
        menu_repertory = kwargs.get(repertory_kwarg)
        _kwargs = {repertory_kwarg: menu_repertory}
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


class FlatPageView(ListView):
    model = FlatPage
    paginate_by = 1
    allow_empty = False

    def get(self, request, *args, **kwargs):
        menu_repertory = kwargs.get(repertory_kwarg)
        _kwargs = {repertory_kwarg: menu_repertory}
        self.menu_context = MenuDetailView.as_view()(request, **_kwargs)

        super(FlatPageView, self).get(request, *args, **kwargs)

        self.object_list = self.get_queryset().filter(menu=self.menu_context['page_menu_object']).select_related('user')
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            # When pagination is enabled and object_list is a queryset,
            # it's better to do a cheap query than to load the unpaginated
            # queryset in memory.
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.") % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data()

        paginated_object = context['object_list']

        if all(item.registration_required for item in paginated_object) and not request.user.is_authenticated:
            return redirect_to_login(request.path)

        return self.render_to_response(context)
