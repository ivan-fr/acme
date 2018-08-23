from django.views.generic.detail import DetailView, SingleObjectMixin
from django.db.models import Count
from django.views.generic.base import RedirectView
from django.http import Http404
from django.contrib.sites.shortcuts import get_current_site

from page.utils import NodeViewManager, MPNodeTreeViewManager
from page.models import Menu

repertory_kwarg, repertory_demarcation = 'page_menu_repertory_path', ':'


class MenuDetailView(DetailView):
    model = Menu
    slug_url_kwarg = repertory_kwarg

    def __init__(self, **kwargs):
        super(MenuDetailView, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        site = get_current_site(request)

        mp_nt_manager = MPNodeTreeViewManager(repertory_demarcation=repertory_demarcation,
                                              repertory=kwargs.get(self.slug_url_kwarg),
                                              model=self.model)

        self.kwargs[self.slug_url_kwarg] = mp_nt_manager.get_main_slug()
        self.object = self.get_object(self.get_queryset().filter(site=site).select_related('site'))

        context = mp_nt_manager(self.object)

        return context


class MenuRedirectView(RedirectView, SingleObjectMixin):
    model = Menu
    slug_url_kwarg = repertory_kwarg

    def __init__(self, **kwargs):
        self.related_fields = tuple(field for field in self.model._meta._get_fields(forward=False))
        super(MenuRedirectView, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        n_manager = NodeViewManager(repertory_demarcation=repertory_demarcation,
                                    repertory=kwargs.get(self.slug_url_kwarg),
                                    model=self.model)

        self.kwargs[self.slug_url_kwarg] = n_manager.get_main_slug()

        count_annotations = []
        for related_field in self.related_fields:
            count_annotations.append(Count(related_field.name, distinct=True))

        menu = self.get_object(self.get_queryset()
                               .filter(site=get_current_site(request))
                               .annotate(*count_annotations))

        i = 0
        while i <= len(self.related_fields) - 1:
            if int(getattr(menu, self.related_fields[i].name + '__count')) > 0:
                self.pattern_name = n_manager.get_related_pattern_name(
                    self.related_fields[i].related_model._meta.app_label,
                    self.related_fields[i].related_model._meta.model_name)
                break
            if i == len(self.related_fields) - 1:
                raise Http404('No match logical forward.')
            i += 1

        return super(MenuRedirectView, self).get(request, *args, **kwargs)
