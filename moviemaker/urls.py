from django.conf.urls.defaults import *
from moviemaker.views import camera_moviecache, camera_search, moviecachefile_subtitles

urlpatterns = patterns('moviemaker.views',
    (r'^camera/(?P<slug>[-\w]+)/?$', camera_moviecache),
    (r'^camera/(?P<slug>[-\w]+)/search/?$', camera_search),
    (r'^moviecachefile/(?P<movie_id>\d+)/(?P<start_cc>\d+)/(?P<end_cc>\d+)/subtitles.xml',\
            moviecachefile_subtitles),
)
