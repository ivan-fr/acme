from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin as FlatPageAdminOld
from django.utils.translation import ugettext_lazy as _
from django.contrib.flatpages.models import FlatPage as OldFlatPage
from django.contrib.sites.shortcuts import get_current_site

from publication.models import FlatPage, Entry
from publication.forms import FlatpageForm, EntryForm


class AdminFormWithRequest(object):
    def get_form(self, request, obj=None, **kwargs):
        admin_form = super(AdminFormWithRequest, self).get_form(request, obj, **kwargs)

        class _AdminFormWithRequest(admin_form):
            def __new__(cls, *args, **kwargs_bis):
                try:
                    kwargs_bis['initial'].update({'site': get_current_site(request)})
                except KeyError:
                    kwargs_bis['initial'] = {'site': get_current_site(request)}
                kwargs_bis['request'] = request
                return admin_form(*args, **kwargs_bis)

        return _AdminFormWithRequest


@admin.register(Entry)
class EntryAdmin(AdminFormWithRequest, admin.ModelAdmin):
    form = EntryForm
    list_display = ('title', 'slug', 'is_created', 'is_updated', 'menu')


class FlatPageAdmin(AdminFormWithRequest, FlatPageAdminOld):
    form = FlatpageForm
    list_display = ('url', 'title', 'get_sites')

    fieldsets = (
        (None, {'fields': ('menu', 'url', 'title', 'content', 'sites')}),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields': ('registration_required', 'template_name'),
        }),
    )

    def get_sites(self, obj):
        return "\n".join([p.name for p in obj.sites.all()])


admin.site.unregister(OldFlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
