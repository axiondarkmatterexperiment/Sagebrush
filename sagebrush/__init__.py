__all__ = []

import pkg_resources

import scarab
a_ver = '0.0.0' #note that this is updated in the following block
try:
    a_ver = pkg_resources.get_distribution('sagebrush').version
    print('version is: {}'.format(a_ver))
except:
    print('fail!')
    pass
version = scarab.VersionSemantic()
version.parse(a_ver)
version.package = 'sagebrush'
version.commit = '---'
__all__.append("version")

from .functions import *
from .functions import __all__ as __functions_all
__all__ += __functions_all

from .network_analyzer_fits import *
from .network_analyzer_fits import __all__ as __na_fits_all
__all__ += __na_fits_all
