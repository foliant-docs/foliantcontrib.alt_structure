from __future__ import annotations

import os

from logging import getLogger
from pathlib import PosixPath
from foliant.meta.classes import Meta

# is overridden in set_up_logger

logger = getLogger('flt.alt_structure.generate')

STRUCTURE_KEY = 'structure'
FOLDER_KEY = 'folder'

ROOT_NODE = 'root'
SUBFOLDER_NODE = 'subfolder'


def setdefault_chapter_section(chapter_section: list, section_name: str) -> list:
    '''
    if dictionary with key section_name is already added to chapter_section,
    return it, if not — add it and return.

    :param chapter_section: chapter section, the list which may contain dicts
                            (sections) or strs — chapter filepaths.
    :param section_name: name of the section to be created if missing and returned.

    :returns: requested chapter section.
    '''
    for subsection in chapter_section:
        if isinstance(subsection, dict) and section_name in subsection:
            return subsection[section_name]
    else:
        new_subsection = {section_name: []}
        chapter_section.append(new_subsection)
        return new_subsection[section_name]


class CategoryTree:
    def __init__(self,
                 structure: dict,
                 unmatched_to_root: bool = False,
                 registry: dict = {},
                 subdir_name: str or None = None):
        self.leaves = []
        self.structure = structure
        self.unmatched_to_root = unmatched_to_root
        self.registry = registry
        self.subdir_name = subdir_name
        global logger
        self.logger = logger
        self.logger.debug(f'CategoryTree init: {self.__dict__}')

    def add_leaf(self, name: str, nodes: dict):
        self.logger.debug(f'Adding leaf {name}, nodes: {nodes}')

        nodes = dict(nodes)
        leaf = Leaf(name=name,
                    root=bool(nodes.get(ROOT_NODE, False)),
                    subfolder=nodes.get(SUBFOLDER_NODE))
        if leaf.is_root:
            self.logger.debug(f'adding to root {leaf}')
            self.leaves.append(leaf)
            return

        cur_level = self.structure
        while True:
            if not isinstance(cur_level, dict):
                # reached end of structure tree
                break
            for key, val in nodes.items():
                if key in cur_level:
                    leaf.add_category(val)
                    cur_level = cur_level[key]
                    break
            else:
                # no more matching nodes
                break
            nodes.pop(key)

        self.leaves.append(leaf)
        self.logger.debug(f'adding {leaf}, categories: {leaf.categories}')

    def render(self) -> list:
        def render_leaf(section: list, leaf: Leaf):
            if leaf.subfolder:
                section = setdefault_chapter_section(section, leaf.subfolder)
            if self.subdir_name:
                name = os.path.join(self.subdir_name, leaf.name)
            else:
                name = leaf.name
            section.append(name)
        result = []
        for leaf in self.leaves:
            if leaf.is_root:
                render_leaf(result, leaf)
            else:
                if not (leaf.categories or self.unmatched_to_root):
                    continue
                current_section = result
                for category in leaf.categories:
                    category_name = self.registry.get(category, category)
                    current_section = setdefault_chapter_section(current_section,
                                                                 category_name)
                render_leaf(current_section, leaf)
        return result


class Leaf:
    def __init__(self,
                 name: str,
                 root: bool,
                 subfolder: str or None = None):
        self.name = name
        self.subfolder = subfolder
        self.categories = []
        self.is_root = root

    def add_category(self, name: str):
        self.categories.append(name)

    def __repr__(self):
        return f'Leaf({self.name}, {self.is_root}, {self.subfolder})'


def gen_chapters(meta: Meta,
                 registry: dict,
                 structure: list,
                 unmatched_to_root: bool,
                 subdir_name: str or None = None
                 ) -> list:
    '''
    Create a chapters list from scratch based on structure defined in metadata
    and structure strings from config.

    :param meta: Meta object with metadata of the project.
    :param registry: dictionary with definitions of node refs from config.
    :param structure: list of structure strings or structure lists from config.
    :param subdir_name: name of the subdir in sr for the new chapter paths

    :returns: generated chapters list.
    '''

    logger.debug(f'Got registry: {registry}')

    tree = CategoryTree(structure, unmatched_to_root, registry, subdir_name)

    for chapter in meta.chapters:
        nodes = chapter.main_section.data.get('structure', {})
        tree.add_leaf(chapter.name, nodes)
    return tree.render()
