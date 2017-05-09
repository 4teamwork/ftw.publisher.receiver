from ftw.builder import builder_registry
from ftw.builder.archetypes import ArchetypesBuilder


class FormGenBuilder(ArchetypesBuilder):
    portal_type = 'FormFolder'

builder_registry.register('form folder', FormGenBuilder)


class SaveDataBuilder(ArchetypesBuilder):
    portal_type = 'FormSaveDataAdapter'

builder_registry.register('save data adapter', SaveDataBuilder)
