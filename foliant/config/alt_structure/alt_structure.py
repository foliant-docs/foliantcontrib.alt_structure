from pathlib import Path
from yaml import add_constructor, load, BaseLoader

from foliant.config.base import BaseParser
from foliant.meta.generate import load_meta
from foliant.preprocessors.utils.combined_options import Options

from .generate import gen_chapters

CONFIG_SECTION = 'alt_structure'
PREPROCESSOR_NAME = 'alt_structure'
CONTEXT_FILE_NAME = '.alt_structure.yml'  # in __folianttmp__
DEFAULT_SEP = '/'


class Parser(BaseParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open(self.config_path) as config_file:
            self.config = {**self._defaults, **load(config_file, Loader=BaseLoader)}

        add_constructor('!alt_structure', self._resolve_tag)

    def _get_config(self) -> dict:
        self.logger.debug('Getting config for alt_structure')
        if CONFIG_SECTION not in self.config:
            raise RuntimeError('Config for alt_structure is not specified!')
        parser_config = Options(self.config[CONFIG_SECTION],
                                required=('structure',),
                                defaults={'sep': DEFAULT_SEP,
                                          'add_unmatched_to_root': False})
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

        if self.need_subdir:
            self.logger.debug('Preprocessor alt_structure is stated, tag will be resolved by it')
            return None  # alt_structure will be built by preprocessor

        src_dir = Path(self.config['src_dir']).expanduser()
        chapters = loader.construct_sequence(node)

        # hack for accepting aliases in yaml [*alias]
        if len(chapters) == 1 and isinstance(chapters[0], list):
            chapters = loader.construct_sequence(node.value[0])

        structure = self.parser_config['structure']
        sep = self.parser_config['sep']
        registry = self.parser_config.get('registry', {})
        meta = load_meta(chapters, src_dir)
        unmatched_to_root = self.parser_config['add_unmatched_to_root']

        self.logger.debug(f'Resolving !alt_structure tag')

        result = gen_chapters(meta,
                              registry,
                              structure,
                              sep,
                              src_dir,
                              unmatched_to_root)

        self.logger.debug(f'Generated alt_structure: {result}')

        return result
