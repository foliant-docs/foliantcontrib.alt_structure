from shutil import copytree

from yaml import load, add_constructor, Loader

from foliant.meta.generate import load_meta
from foliant.preprocessors.base import BasePreprocessor
from foliant.config.alt_structure.generate import gen_chapters
from foliant.config.alt_structure.alt_structure import CONFIG_SECTION, DEFAULT_SEP
from foliant.preprocessors.utils.combined_options import Options


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
                                     defaults={'sep': DEFAULT_SEP,
                                               'add_unmatched_to_root': False})
        self.tag_count = 0

        # redefining alt_structure tag constructor
        add_constructor('!alt_structure', self._resolve_tag)

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

    def _resolve_tag(self, loader, node) -> str:
        '''
        Resolve !alt_structure tag in foliant config. The tag accepts list of
        chapters and returns new structure based on metadata and alt_structure
        config.
        '''
        chapters = loader.construct_sequence(node)

        # hack for accepting aliases in yaml [*alias]
        if len(chapters) == 1 and isinstance(chapters[0], list):
            chapters = loader.construct_sequence(node.value[0])

        structure = self.parser_config['structure']
        sep = self.parser_config['sep']
        registry = self.parser_config.get('registry', {})
        meta = load_meta(chapters, self.working_dir)
        unmatched_to_root = self.parser_config['add_unmatched_to_root']

        self.logger.debug(f'Resolving !alt_structure tag again')

        self.tag_count += 1
        self.logger.debug(f'Total times !alt_structure used = {self.tag_count}')

        subdir = self._gen_subdir(self.tag_count)
        self.logger.debug(f'Subdir: {subdir}')

        result = gen_chapters(meta,
                              registry,
                              structure,
                              sep,
                              self.working_dir,
                              unmatched_to_root,
                              subdir)

        self.logger.debug(f'Generated alt_structure: {result}')

        return result

    def apply(self):
        self.logger.debug('Applying preprocessor')

        if not self.options['create_subfolders']:
            self.logger.debug('`create_subfolders` is False, nothing to do')
            return

        config_file_name = self.context.get('config_file_name', 'foliant.yml')
        with open(config_file_name) as c:
            new_config = load(c, Loader)
        self.context['config']['chapters'] = new_config['chapters']

        self.logger.debug('Preprocessor applied')
