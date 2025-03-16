__all__ = []

import pkg_resources

import scarab
a_ver = '0.0.0' #note that this is updated in the following block
try:
    a_ver = pkg_resources.get_distribution('jitter_plugin').version
    print('version is: {}'.format(a_ver))
except:
    print('fail!')
    pass
version = scarab.VersionSemantic()
version.parse(a_ver)
version.package = 'driplineorg/controls-guide/jitter_plugin'
version.commit = '---'
__all__.append("version")

from .repeat_provider import *
from .repeat_provider import __all__ as __repeat_provider_all
from .format_entity_extra import *
from .format_entity_extra import __all__ as __format_entity_extra_all
__all__ += __repeat_provider_all
__all__ += __format_entity_extra_all

