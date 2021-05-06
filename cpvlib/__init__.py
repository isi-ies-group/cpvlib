from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution('cpvlib').version
except DistributionNotFound:
     # package is not installed
    pass

from cpvlib import cpvsystem
