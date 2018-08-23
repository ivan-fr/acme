from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from treebeard.mp_tree import MP_Node, MP_MoveHandler, MP_AddRootHandler, MP_AddChildHandler, InvalidMoveToDescendant

neutral = 'ne'
navigator, sub_navigator = 'n', 'sn'
top, bottom = 't', 'b'

NODE_TYPE_CHOICES = ((navigator, 'navigator'), (sub_navigator, 'sub-navigator'), (neutral, 'neutral'))
NODE_HTML_VERTICAL_POS_CHOICES = ((top, 'top'), (bottom, 'bottom'), (neutral, 'neutral'))


class SiteMPMoveHandler(MP_MoveHandler):
    def update_move_to_child_vars(self):

        if not self.target.site == self.node.site:
            raise InvalidMoveToDescendant(_('The parent/sibling is not in the same website.'))

        if self.pos in ('first-child', 'last-child', 'sorted-child'):
            if self.node.type == navigator:
                raise InvalidMoveToDescendant(_("A navigator have to be a fully-root children."))
        else:
            if (self.target is None or self.target.is_root()) and not self.node.type == navigator:
                raise InvalidMoveToDescendant(_("The parent cannot be the fully-root "
                                                "if your menu is sub-navigator or neutral."))
            elif not(self.target is None or self.target.is_root()) and self.node.type == navigator:
                raise InvalidMoveToDescendant(_("A navigator have to be a fully-root children."))

        return super(SiteMPMoveHandler, self).update_move_to_child_vars()


class SiteMPAddRootHandler(MP_AddRootHandler):
    def process(self):
        if len(self.kwargs) == 1 and 'instance' in self.kwargs:
            if not self.kwargs['instance'].type == navigator:
                raise InvalidMoveToDescendant(_("The parent cannot be the fully-root "
                                                "if your menu is sub-navigator or neutral."))
        else:
            if not self.kwargs['type'] == navigator:
                raise InvalidMoveToDescendant(_("The parent cannot be the fully-root "
                                                "if your menu is sub-navigator or neutral."))
        return super(SiteMPAddRootHandler, self).process()


class SiteMPAddChildHandler(MP_AddChildHandler):
    def process(self):
        if len(self.kwargs) == 1 and 'instance' in self.kwargs:
            if not self.node.site == self.kwargs['instance'].site:
                raise InvalidMoveToDescendant(_('The parent/sibling is not in the same website.'))

            if self.kwargs['instance'].type == navigator:
                raise InvalidMoveToDescendant(_("A navigator have to be a fully-root children."))
        else:
            if not self.node.site == self.kwargs['site']:
                raise InvalidMoveToDescendant(_('The parent/sibling is not in the same website.'))

            if self.kwargs['type'] == navigator:
                raise InvalidMoveToDescendant(_("A navigator have to be a fully-root children."))

        return super(SiteMPAddChildHandler, self).process()


class Menu(MP_Node):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    type = models.CharField(choices=NODE_TYPE_CHOICES, default=neutral, max_length=2)
    vertical_position = models.CharField(choices=NODE_HTML_VERTICAL_POS_CHOICES,
                                         default=neutral,
                                         max_length=2,
                                         help_text='Choice the HTML vertical position of '
                                                   'this menu if he is a navigator.')
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    @classmethod
    def add_root(cls, **kwargs):
        return SiteMPAddRootHandler(cls, **kwargs).process()

    def move(self, target, pos=None):
        return SiteMPMoveHandler(self, target, pos).process()

    def add_child(self, **kwargs):
        return SiteMPAddChildHandler(self, **kwargs).process()

    class Meta:
        unique_together = ('path', 'site')
