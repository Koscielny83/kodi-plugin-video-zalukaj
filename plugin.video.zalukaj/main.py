# -*- coding: utf-8 -*-

import xbmcaddon

from resources.lib import kodilogging
from resources.lib import plugin

# Keep this file to a minimum, as Kodi
# doesn't keep a compiled copy of this
ADDON = xbmcaddon.Addon()
kodilogging.config()

plugin.run()
