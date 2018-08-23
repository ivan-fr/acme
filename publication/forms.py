from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms
from django.contrib.flatpages.forms import FlatpageForm as FlatpageFormOld
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from page.models import Menu
from publication.models import Entry, FlatPage


class IndentModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return mark_safe('&nbsp;&nbsp;&nbsp;&nbsp;' * (obj.depth - 1) + escape(obj).capitalize())


class EntryForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())
    menu = IndentModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):

        site = kwargs['initial'].pop('site')
        self.request = kwargs.pop('request')
        super(EntryForm, self).__init__(*args, **kwargs)

        self.fields['menu'].queryset = Menu.get_tree().filter(site=site)

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

        site = kwargs['initial'].pop('site')
        self.request = kwargs.pop('request')
        super(FlatpageForm, self).__init__(*args, **kwargs)

        self.fields['menu'].queryset = Menu.get_tree().filter(site=site)

        mutable = self.request.POST._mutable
        self.request.POST._mutable = True
        self.request.POST._mutable = mutable

    class Meta:
        model = FlatPage
        fields = ('url', 'title', 'content', 'menu', 'sites', 'enable_comments', 'template_name')

    def clean_url(self):
        menu = self.cleaned_data['menu']
        slugs = []
        for parent in menu.get_ancestors():
            slugs.append(parent.slug)
        slugs.append(menu.slug)
        url = '/' + '/'.join(slugs) + '/'
        return url

    def clean(self):
        menu = self.cleaned_data.get('menu')
        if menu.site not in self.cleaned_data.get('sites', ()):
            self.cleaned_data['sites'] = tuple(self.cleaned_data.get('sites', ())) + (menu.site,)
        raise KeyError(self.data)
        return super(FlatpageForm, self).clean()

    def save(self, commit=True):
        self.instance.user = self.request.user
        return super(FlatpageForm, self).save(commit)
