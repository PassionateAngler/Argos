import os
from django.utils.log import getLogger
dir = os.path.dirname(__file__)

MOVIECACHE_URL = 'http://<host>:<port>/moviecache'

MENCODER_PATH='/usr/bin/mencoder'
MENCODER_LAVCOPTS='vcodec=flv:keyint=1:vbitrate=300:mbd=2:mv0:trell:v4mv:cbp:last_pred=3'
MENCODER_CMD = lambda src,dst:"%s \
mf://@%s \
-mf fps=1:type=jpg \
-ovc lavc \
-of lavf \
-lavcopts %s \
-quiet \
-o %s"%(MENCODER_PATH, src, MENCODER_LAVCOPTS, dst)

FLVTOOL2_PATH='/usr/bin/flvtool2'

MOVIE_CACHE_DIR=os.path.join(dir,'moviecache')
MOVIE_MAX_LENGHT = 3600
MOVIE_MIN_LENGTH = 300

MOVIE_NAME_REGEXP = r"""
(?P<year_s>\d{4})(?P<month_s>\d{2})(?P<day_s>\d{2})_ 
(?P<h_s>\d{2})(?P<m_s>\d{2})(?P<s_s>\d{2})_
(?P<duration>\d+)_
(?P<year_e>\d{4})(?P<month_e>\d{2})(?P<day_e>\d{2})_
(?P<h_e>\d{2})(?P<m_e>\d{2})(?P<s_e>\d{2})
_(?P<name>\w+)\.flv"""

MEDIA_LOGGER = getLogger('media')
ARGOS_LOGGER = getLogger('argos')

#number of slices (for every boundry of search) to show as closest 
MAX_SLICE_NUMBER = 3 
