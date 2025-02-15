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

from .multi_format import *
from .multi_format import __all__ as __multi_format_all
__all__ += __multi_format_all

