import os
from shutil import copytree

from yaml import load, Loader

from foliant.meta.generate import load_meta
from foliant.preprocessors.base import BasePreprocessor
from foliant.config.alt_structure.generate import gen_chapters
from foliant.config.alt_structure.alt_structure import (CONFIG_SECTION,
                                                        PLACEHOLDER,
                                                        CONTEXT_FILE_NAME)
from foliant.preprocessors.utils.combined_options import Options


def load_chapters_from_context(id_: int) -> list:
    '''
    Load chapters list from context file and return them.

    :param id_: key for the chapter list in context.

    :returns: chapter list from context file
    '''

    if not os.path.exists(CONTEXT_FILE_NAME):
        return []
    with open(CONTEXT_FILE_NAME, encoding='utf8') as f:
        context = load(f, Loader)
    return context.get(id_, [])


def walk_chapters(val: list or dict or str, func):
    '''
    Walk chapter tree in search of alt_structure placeholders. On place of each
    placeholder put the result of func. func should accept one parameter —
    the placeholder value.

    Recursive, in place.

    :param val: chapters list to process
    :param func: function which will be applied to placeholders
    '''

    if isinstance(val, str):
        if val.startswith(PLACEHOLDER.format(id='')):
            return func(val)
        else:
            return val
    elif isinstance(val, list):
        for i in range(len(val)):
            val[i] = walk_chapters(val[i], func)
        return val
    elif isinstance(val, dict):
        for key in val.keys():
            val[key] = walk_chapters(val[key], func)
        return val


class Preprocessor(BasePreprocessor):
    defaults = {
        'create_subfolders': True
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = self.logger.getChild('alt_structure')
        self.logger.debug(f'Preprocessor inited: {self.__dict__}')
        self.parser_config = Options(self.config[CONFIG_SECTION],
                                     required=('structure',),
                                     defaults={'add_unmatched_to_root': False})
        self.tag_count = 0

    def _gen_subdir(self, count: int) -> str:
        '''
        Generate subdir name based on `count` param and copy the entire
        working_dir into it.

        :param count: number of times alt_structure tag used. Used to generate
                      subdir name.

        :returns: generated subdir name.
        '''
        subdir_name = f'alt{count}'
        copytree(self.working_dir, self.working_dir / subdir_name)
        return subdir_name

    def _process_tag(self, placeholder: str) -> list:
        '''
        Resolve alt_structure placeholder in foliant config.

        :param placeholder: placeholder from the chapters list.

        :returns: alternative structure list.
        '''

        id_ = int(placeholder[len(PLACEHOLDER.format(id=''))])
        chapter_list = load_chapters_from_context(id_)

        self.logger.debug(f'Got list  of chapters from context: {chapter_list}')

        structure = self.parser_config['structure']
        registry = self.parser_config.get('registry', {})
        meta = load_meta(chapter_list, self.working_dir)
        unmatched_to_root = self.parser_config['add_unmatched_to_root']

        self.logger.debug(f'Resolving !alt_structure tag again')

        self.tag_count += 1
        self.logger.debug(f'Total times !alt_structure used = {self.tag_count}')

        subdir = self._gen_subdir(self.tag_count)
        self.logger.debug(f'Subdir: {subdir}')

        result = gen_chapters(meta,
                              registry,
                              structure,
                              unmatched_to_root,
                              subdir)

        self.logger.debug(f'Generated alt_structure: {result}')

        return result

    def apply(self):
        self.logger.debug('Applying preprocessor')

        if not self.options['create_subfolders']:
            self.logger.debug('`create_subfolders` is False, nothing to do')
            return

        walk_chapters(self.context['config'].get('chapters', []), self._process_tag)

        self.logger.debug(
            f"chapters after preprocessor:\n\n{self.context['config'].get('chapters', [])}"
        )

        self.logger.debug('Preprocessor applied')
