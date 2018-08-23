from page.models import navigator, sub_navigator, neutral
from django.db.models import Q
from django.http import Http404
from treebeard.mp_tree import MP_Node


def _separator(string, separator, _type):
    if _type is tuple:
        slug_list = ()
    else:
        slug_list = []

    if string:
        cursor, i, string = 0, 0, string + separator
        while i <= len(string) - 1:
            if string[i] == separator:
                if i - 1 >= cursor:
                    if _type is tuple:
                        slug_list = slug_list + (string[cursor:i],)
                    else:
                        slug_list.append(string[cursor:i])
                delta = 1
                while i + delta <= len(string) - 1:
                    if separator != string[i + delta]:
                        break
                    delta += 1
                i = cursor = i + delta
            i += 1
    return slug_list


def _get_q_filter_from_conditions(conditions):
    if isinstance(conditions, list):
        q_complex = conditions.pop()
        for condition in conditions:
            if isinstance(condition, Q):
                q_complex |= condition
        return q_complex
    raise TypeError()


actived_reference_slug_kwarg = 'actived_reference_slug'


class NodeViewManager(object):
    def __init__(self, repertory_demarcation, repertory, model):
        assert issubclass(model, MP_Node)

        self.model = model

        self.repertory_slugs = ()
        self.repertory_demarcation = repertory_demarcation
        self.__extract_slugs_from_repertory(repertory)

    def __extract_slugs_from_repertory(self, repertory):
        if not self.repertory_slugs:
            self.repertory_slugs = _separator(repertory, self.repertory_demarcation, tuple)

    def get_related_pattern_name(self, related_app_label, related_model_name):
        return ':'.join((self.model._meta.app_label, related_app_label, related_model_name))

    def get_main_slug(self):
        return self.repertory_slugs[-1]


class MPNodeTreeViewManager(NodeViewManager):
    def __init__(self, repertory_demarcation, repertory, model):
        super(MPNodeTreeViewManager, self).__init__(repertory_demarcation, repertory, model)

        self.reference_slug = None

        self.context = {}
        self.context_prefix = '_'.join(iter((self.model._meta.app_label, self.model._meta.model_name, '')))

        self.__set_context('repertory', repertory)

        self.nodes_for_descendants_performing = []
        self.added_reference = False

    def __call__(self, main_node):
        return self.__perform_concoction(main_node)

    def __get_typed_annotated_menu(self, parent_node):
        if parent_node.type != navigator:
            return self.__get_annotated_list_from_parent(parent_node)

        sub_navigators = parent_node.get_descendants().filter(type=sub_navigator)

        # sn_ = ((path, depth), ..., (path, depth))
        sub_navigators = sub_navigators.values_list('path', 'depth')

        if len(sub_navigators) == 0:
            return self.__get_annotated_list_from_parent(parent_node, max_depth=parent_node.depth + 1)

        n_sn_data = {parent_node.depth: {parent_node.path: [parent_node.path]}}
        # Ici on complete le n_sn_data
        i, n_sn_path, excluded_sn = 0, (parent_node.path,) + tuple(values[0] for values in sub_navigators), []
        while i <= len(sub_navigators) - 1:

            current_sn_path, current_sn_depth = sub_navigators[i][0], sub_navigators[i][1]
            current_sn_basepath = self.model._get_basepath(current_sn_path, current_sn_depth - 1)

            j, possible_parent_n_sn_path = 0, tuple(set(n_sn_path) - {current_sn_path} - set(excluded_sn))
            while j <= len(possible_parent_n_sn_path) - 1:

                # On verife si current_sn est l'enfant des parents disponible
                if possible_parent_n_sn_path[j] == current_sn_basepath:
                    # Ici current_sn est l'enfant direct d'un sub-navigator ou d'un navigator
                    # Le parent étant à depth - 1 à la valeur de basepath. On lui ajoute current_sn_path.
                    n_sn_data[current_sn_depth - 1][current_sn_basepath] += [current_sn_path]

                    # Ensuite on crée une clé de possibilité
                    try:
                        n_sn_data[current_sn_depth][current_sn_path] = []
                    except KeyError:
                        n_sn_data[current_sn_depth] = {current_sn_path: []}
                    break

                if j == len(possible_parent_n_sn_path) - 1:
                    # Ici aucun parent sb ou n n'a été trouvé donc ce sn n'est pas un parent valide.
                    excluded_sn.append(current_sn_path)
                j += 1

            i += 1

        # On génère ensuite le queryset correspondant
        i, n_sn_data, conditions = 0, list(n_sn_data.items()), []
        while i <= len(n_sn_data) - 1:
            j, complex_data, depth_n_sn_ = 0, list(n_sn_data[i][1].items()), n_sn_data[i][0]
            while j <= len(complex_data) - 1:
                conditions.append(Q(path__startswith=complex_data[j][0], depth__gte=depth_n_sn_,
                                    depth__lte=depth_n_sn_ + 1) & ~Q(path__in=complex_data[j][1]))
                j += 1
            i += 1

        queryset = self.model.objects.filter(_get_q_filter_from_conditions(conditions))
        return self.__get_annotated_list_from_parent(parent_node, queryset=queryset)

    def __get_annotated_list_from_parent(self, parent_node, max_depth=None, queryset=None):
        if queryset is None:
            queryset = parent_node.get_descendants()

            if max_depth:
                queryset = queryset.filter(depth__lte=max_depth)

        node_info = self.model.get_annotated_list_qs(queryset)

        if parent_node.slug == self.reference_slug == self.repertory_slugs[-1]:
            slug_repertory = self.repertory_slugs
        else:
            slug_repertory = [parent_node.slug]

            if not parent_node.is_root():
                slug_repertory = [menu.slug for menu in parent_node.get_ancestors()] + slug_repertory

        i, level, prev_level = 0, 0, None
        while i <= len(node_info) - 1:

            node, level = node_info[i][0], node_info[i][1]['level']

            # creating repertory info key
            if prev_level is not None:
                if level == prev_level:
                    slug_repertory = slug_repertory[:-1]
                elif level <= prev_level - 1:
                    slug_repertory = slug_repertory[:level - prev_level - 1]
            slug_repertory.append(node.slug)
            node_info[i][1]['repertory'] = self.repertory_demarcation.join(slug_repertory)

            # creating "next is level up ?" key info
            try:
                next_node_info = node_info[i + 1]
                node_info[i][1]['next_level_up'] = next_node_info[1]['level'] > level
            except IndexError:
                node_info[i][1]['next_level_up'] = False

            node_info[i][1]['active_repertory'] = node.slug in self.repertory_slugs

            # creating "level target"
            node_info[i][1]['level_target'] = node_info[i][1]['level'] - len(node_info[i][1]['close'])

            prev_level = level

            i += 1
        return node_info

    def __perform_concoction(self, main_node):
        assert self.added_reference is False
        self.added_reference = True

        self.__set_context('object', main_node)

        ancestors = [{'name': menu.name, 'slug': menu.slug, 'type': menu.type} for menu in main_node.get_ancestors()]
        ancestors.append({'name': main_node.name, 'slug': main_node.slug, 'type': main_node.type})

        main_slug_ancestors = tuple(ancestor['slug'] for ancestor in ancestors)

        if main_slug_ancestors != self.repertory_slugs:
            raise Http404(str(self.repertory_slugs), str(main_slug_ancestors))

        i, reference_slug = 0, None
        while i <= len(ancestors) - 1:
            if i <= len(ancestors) - 2 and (ancestors[i]['type'] == navigator or ancestors[i]['type'] == sub_navigator):
                reference_slug = self.repertory_slugs[i + 1]
            ancestors[i]['repertory'] = self.repertory_demarcation.join(self.repertory_slugs[:i + 1])
            i += 1

        self.__set_context('breadcrumb', ancestors)
        self.__set_context('reference_slug', reference_slug)

        self.reference_slug = reference_slug

        self.nodes_for_descendants_performing.append(Q(type=navigator))
        self.nodes_for_descendants_performing.append(Q(slug=reference_slug, type=neutral))

        menus = self.model.objects.filter(_get_q_filter_from_conditions(self.nodes_for_descendants_performing),
                                          site=main_node.site).distinct()

        if len(menus) > 0:
            for menu in menus:
                self.__set_context('_'.join(iter((menu.type, menu.vertical_position))),
                                   self.__get_typed_annotated_menu(menu), menu)
            return self.context
        raise Exception()

    def __set_context(self, key, data, node=None):
        key_name = self.context_prefix + key

        if node is not None and node.type == navigator:
            try:
                self.context[key_name].append(data)
            except KeyError:
                self.context[key_name] = [data]
        else:
            self.context[key_name] = data
