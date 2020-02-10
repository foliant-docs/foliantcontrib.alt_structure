import os
from pathlib import PosixPath, Path
from foliant.meta.classes import Section, Meta

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


def add_chapter(section: Section,
                chapters: list,
                nodes: list,
                registry: dict,
                src_dir: PosixPath or str,
                subfolder: str or None,
                subdir_name: str or None):
    '''
    Add a chapter to a list of chapters. The structure is generated from the
    list of nodes (and subfolder, if present), node names are looked up in the
    registry. Path to file is taken from meta section, relative to src_dir.
    If subdir_name specified, it will be added to the beginning of all paths.

    :param section: main meta section for the chapter which is being added.
    :param chapters: list of chapters where the chapter will be added.
    :param nodes: list of nodes from which the chapter structure will be generated.
    :param registry: dictionary with key = alias, used in meta, value = verbose
                     title to be used in chapters.
    :param src_dir: directory relative to which the metadata was generated (to
                    determine the correct paths to insert into chapters)
    :param subfolder: lowest category title to be inserted into chapters before
                      current chapter. If falsy — ignored.
    :param subdir_name: name of the subdirectory which will be inserted into the
                        beginning of the chapter path.
    '''
    current_list = chapters
    for i in range(len(nodes)):
        node = nodes[i]
        node_ref = section.data['structure'][node]
        node_descr = registry.get(node, {}).get(node_ref) or node_ref
        current_list = setdefault_chapter_section(current_list, node_descr)
    if subfolder:
        current_list = setdefault_chapter_section(current_list, subfolder)
    chapter_name = str(Path(section.filename).relative_to(src_dir))
    if subdir_name:
        chapter_name = os.path.join(subdir_name, chapter_name)
    if chapter_name not in current_list:
        current_list.append(chapter_name)


def get_node_list(branch: str or list, sep='/'):
    """
    Parse branch if it is a string and split it into list of nodes. Check if
    special names weren't uses in nodes and return the list.

    :param branch: one structure string to be split or list of strings
    :param sep: separator, used to split the structure string (ignored for list)

    :returns: list of node names
    """
    special_nodes = (ROOT_NODE, SUBFOLDER_NODE)
    if isinstance(branch, str):
        result = branch.split(sep)
    elif isinstance(branch, list):
        result = branch
    else:
        RuntimeError('Structure element should be either a string or a list.'
                     f'You supplied {branch}')

    for node in result:
        if node in special_nodes:
            RuntimeError(f"Sorry, {node} is a special name, you can't use it in"
                         'structure')
    return result


def gen_chapters(meta: Meta,
                 registry: dict,
                 structure: list,
                 sep: str,
                 src_dir: PosixPath or str,
                 unmatched_to_root: bool,
                 subdir_name: str or None = None
                 ) -> list:
    '''
    Create a chapters list from scratch based on structure defined in metadata
    and structure strings from config.

    :param meta: Meta object with metadata of the project.
    :param registry: dictionary with definitions of node refs from config.
    :param structure: list of structure strings or structure lists from config.
    :param sep: separator for structure strings (ignored if structure is a list)
    :param src_dir: source dir, relative to which paths will be added to chapters
    :param subdir_name: name of the subdir in sr for the new chapter paths

    :returns: generated chapters list.
    '''
    chapters = []
    unmatched = []
    root = []

    # branch is a single structure template, e.g.: "topic/entity"
    for branch in structure:
        # node is one level of structure, e.g.: "topic"
        node_list = get_node_list(branch)
        # start with single node, then incrementally add other nodes
        for i in range(len(node_list) + 1):
            match = node_list[:i]

            next_node = node_list[i] if i < len(node_list) else None
            for chapter in meta.chapters:
                section = chapter.main_section

                # nodes, defined for this chapter
                structure = dict(section.data.get('structure', {}))

                # special nodes treatment
                is_root = False
                if ROOT_NODE in structure:
                    structure.pop(ROOT_NODE)
                    is_root = True
                subfolder = None
                if SUBFOLDER_NODE in structure:
                    subfolder = structure.pop(SUBFOLDER_NODE)

                # save root articles
                if i == 0:
                    if is_root:
                        if section not in root:
                            root.append(section)
                    elif section not in unmatched:
                        unmatched.append(section)

                # check if all `match` nodes are in section structure and next
                # by order node is _not_ in there
                elif set(match).issubset(structure) and next_node not in structure:
                    add_chapter(section,
                                chapters,
                                match,
                                registry,
                                src_dir,
                                subfolder,
                                subdir_name)
                    if section in unmatched:
                        unmatched.pop(unmatched.index(section))
                    if section in root:
                        root.pop(root.index(section))

    to_root = [*root, *unmatched] if unmatched_to_root else root
    for section in to_root:
        add_chapter(section,
                    chapters,
                    [],
                    registry,
                    src_dir,
                    subfolder,
                    subdir_name)
    return chapters
