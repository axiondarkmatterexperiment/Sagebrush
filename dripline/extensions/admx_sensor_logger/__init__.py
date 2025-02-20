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
version.package = 'sagebrush'
version.commit = '---'
__all__.append("version")

from .admx_sensor_logger import *
from .admx_sensor_logger import __all__ as __admx_sensor_logger_all
__all__ += __admx_sensor_logger_all

