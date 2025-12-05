__all__ = []

from .functions import *
from .network_analyzer_fits import *

import logging
logger = logging.getLogger(__name__)

# Here we set sagebrush.__version__ and we give the version object to dl
def __get_version():
    import scarab
    import pkg_resources
    from dripline import core
    #TODO: this all needs to be populated from setup.py and gita
    version = scarab.VersionSemantic()
    logger.info('Sagebrush version should be: {}'.format(pkg_resources.get_distribution('Sagebrush').version))
    version.parse(pkg_resources.get_distribution('Sagebrush').version)
    version.package = 'Sagebrush'
    version.commit = 'na'
    core.add_version('sagebrush', version)
    return version
version = __get_version()
__version__ = version.version
