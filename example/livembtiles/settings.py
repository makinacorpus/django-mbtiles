from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

try:
    from local_settings import *
except ImportError:
    raise ImproperlyConfigured(_('Cannot import any local settings file'))
