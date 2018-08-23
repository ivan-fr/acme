from django.utils.translation import ugettext_lazy as _
from django.forms import ValidationError
from django.forms.models import ErrorList

from page.models import neutral, sub_navigator, navigator

from treebeard.forms import MoveNodeForm


class SitesMoveNodeForm(MoveNodeForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, **kwargs):

        self.site = initial['site']

        super(SitesMoveNodeForm, self).__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix,
            empty_permitted, instance, **kwargs)

    def mk_dropdown_tree(self, model, for_node=None):
        options = [(0, _('-- root --'))]
        for node in model.get_root_nodes().filter(site=self.site):
            self.add_subtree(for_node, node, options)
        return options

    def clean_vertical_position(self):
        if self.cleaned_data['type'] == neutral or self.cleaned_data['type'] == sub_navigator:
            return neutral
        elif self.cleaned_data['vertical_position'] == neutral:
            raise ValidationError('This position cannot be neutral if this '
                                  'menu is a navigator.',
                                  code='ivalid position')
        return self.cleaned_data['vertical_position']

    def clean(self):

        position_type, reference_node_id = self.cleaned_data['_position'], self.cleaned_data['_ref_node_id']

        reference_node = None
        if reference_node_id:
            reference_node = self._meta.model.objects.get(pk=reference_node_id)

        if reference_node and not reference_node.site == self.cleaned_data['site']:
            raise ValidationError(_('The parent/sibling is not in the same website.'))

        if position_type == 'first-child':
            if self.cleaned_data['type'] == navigator and reference_node:
                raise ValidationError(_("A navigator have to be a fully-root children."))
            if not reference_node and not self.cleaned_data['type'] == navigator:
                raise ValidationError(_("The parent cannot be the fully-root "
                                        "if your menu is sub-navigator or neutral."))
        else:
            if (reference_node is None or reference_node.is_root()) and not self.cleaned_data['type'] == navigator:
                raise ValidationError(_("The parent cannot be the fully-root "
                                        "if your menu is sub-navigator or neutral."))
            elif not(reference_node is None or reference_node.is_root()) and self.cleaned_data['type'] == navigator:
                raise ValidationError(_("A navigator have to be a fully-root children."))

        return super(SitesMoveNodeForm, self).clean()
