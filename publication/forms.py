from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib.flatpages.forms import FlatpageForm as FlatpageFormOld
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.contrib.sites.shortcuts import get_current_site

from page.models import Menu
from publication.models import Entry, FlatPage


class IndentModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return mark_safe('&nbsp;&nbsp;&nbsp;&nbsp;' * (obj.depth - 1) + escape(obj).capitalize())


class EntryForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())
    menu = IndentModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')

        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields['menu'].queryset = Menu.get_tree().filter(site=get_current_site(self.request))

    class Meta:
        model = Entry
        fields = ('menu', 'title', 'content')

    def save(self, commit=True):
        self.instance.slug = slugify(self.instance.title)
        self.instance.user = self.request.user
        return super(EntryForm, self).save(commit)


class FlatpageForm(FlatpageFormOld):
    url = None
    content = forms.CharField(widget=CKEditorUploadingWidget())
    menu = IndentModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):

        self.request = kwargs.pop('request')
        super(FlatpageForm, self).__init__(*args, **kwargs)
        self.fields['menu'].queryset = Menu.get_tree().filter(site=get_current_site(self.request))

    class Meta:
        model = FlatPage
        exclude = ('url',)

    def save(self, commit=True):
        self._meta.fields.append('sites')
        self.instance.user = self.request.user

        menu = self.cleaned_data['menu']
        slugs = []
        for parent in menu.get_ancestors():
            slugs.append(parent.slug)
        slugs.append(menu.slug)
        url = '/' + '/'.join(slugs) + '/'
        self.instance.url = url

        self.cleaned_data['sites'] = (menu.site,)

        return super(FlatpageForm, self).save(commit)
