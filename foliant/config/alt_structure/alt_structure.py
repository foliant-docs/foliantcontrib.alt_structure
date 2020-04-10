import os
from pathlib import Path
from yaml import add_constructor, load, dump, BaseLoader, Loader

from foliant.config.base import BaseParser
from foliant.meta.generate import load_meta
from foliant.preprocessors.utils.combined_options import Options

from .generate import gen_chapters

CONFIG_SECTION = 'alt_structure'
PREPROCESSOR_NAME = 'alt_structure'
CONTEXT_FILE_NAME = '.alt_structure.yml'
PLACEHOLDER = '__alt_structure_{id}'


def save_to_context(chapters):
    if os.path.exists(CONTEXT_FILE_NAME):
        with open(CONTEXT_FILE_NAME, encoding='utf8') as f:
            context = load(f, Loader)
    else:
        context = {}
    i = 1
    while i in context:
        i += 1
    context[i] = chapters
    with open(CONTEXT_FILE_NAME, 'w') as f:
        f.write(dump(context))
    return i


class Parser(BaseParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = self.logger.getChild('alt_structure')
        with open(self.config_path) as config_file:
            self.config = {**self._defaults, **load(config_file, Loader=BaseLoader)}

        add_constructor('!alt_structure', self._resolve_tag)

    def _get_config(self) -> dict:
        self.logger.debug('Getting config for alt_structure')
        if CONFIG_SECTION not in self.config:
            raise RuntimeError('Config for alt_structure is not specified!')
        parser_config = Options(self.config[CONFIG_SECTION],
                                required=('structure',),
                                defaults={'add_unmatched_to_root': False})
        self.logger.debug(f'Config for alt_structure: {parser_config}')
        return parser_config

    def _get_need_subdir(self) -> bool:
        '''
        Return True if alt_structure preprocessor is in preprocessors list in config,
        and `create_subfolders` option is turned on (or omited, it is True
        by default).
        Return False in all other cases.
        '''
        for prep in self.config.get('preprocessors', {}):
            if isinstance(prep, str):
                if prep == PREPROCESSOR_NAME:
                    return True
            elif isinstance(prep, dict):
                if PREPROCESSOR_NAME in prep:
                    if prep[PREPROCESSOR_NAME].\
                            get('create_subfolders', False).lower() == 'true':
                        return True
        return False

    def _resolve_tag(self, loader, node) -> str:
        '''
        Resolve !alt_structure tag in foliant config. The tag accepts list of
        chapters and returns new structure based on metadata and alt_structure
        config.
        '''

        self.parser_config = self._get_config()
        self.need_subdir = self._get_need_subdir()

        src_dir = Path(self.config['src_dir'])
        chapter_list = loader.construct_sequence(node)

        # hack for accepting aliases in yaml [*alias]
        if len(chapter_list) == 1 and isinstance(chapter_list[0], list):
            chapter_list = loader.construct_sequence(node.value[0], deep=True)

        self.logger.debug(f'Got list  of chapters: {chapter_list}')

        if self.need_subdir:
            id_ = save_to_context(chapter_list)
            self.logger.debug('Preprocessor alt_structure is stated, tag will be resolved by it.'
                              f' Saving chapters list to context under id {id_}.')
            return PLACEHOLDER.format(id=id_)  # alt_structure will be built by preprocessor

        structure = self.parser_config['structure']
        registry = self.parser_config.get('registry', {})
        meta = load_meta(chapter_list, src_dir)
        unmatched_to_root = self.parser_config['add_unmatched_to_root']

        self.logger.debug(f'Resolving !alt_structure tag')

        result = gen_chapters(meta,
                              registry,
                              structure,
                              unmatched_to_root)

        self.logger.debug(f'Generated alt_structure: {result}')

        return result
