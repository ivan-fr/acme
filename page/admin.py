from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site

from page.models import Menu
from page.forms import SitesMoveNodeForm

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


class SiteFilter(admin.SimpleListFilter):
    title = 'site'
    parameter_name = 'site'

    def lookups(self, request, model_admin):
        sites = [(site.id, site.name) for site in Site.objects.all()]
        return sites

    def queryset(self, request, queryset):
        if self.value() is None:
            site = get_current_site(request)
            self.used_parameters.update({self.parameter_name: str(site.id)})

        return queryset.filter(site__id__exact=self.value())

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }


@admin.register(Menu)
class MenuAdmin(TreeAdmin):
    form = movenodeform_factory(Menu, form=SitesMoveNodeForm, exclude=('site',))
    prepopulated_fields = {'slug': ('name',)}
    list_filter = (SiteFilter,)
    list_display = ('__str__', 'type', 'vertical_position')

    def get_form(self, request, obj=None, **kwargs):
        admin_form = super(MenuAdmin, self).get_form(request, obj, **kwargs)

        class AdminFormWithRequest(admin_form):
            def __new__(cls, *args, **kwargs_bis):
                try:
                    kwargs_bis['initial'].update({'site': get_current_site(request)})
                except KeyError:
                    kwargs_bis['initial'] = {'site': get_current_site(request)}
                return admin_form(*args, **kwargs_bis)

        return AdminFormWithRequest
