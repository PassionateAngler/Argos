#!/usr/bin/env python
import os
import shutil
from subprocess import call
from tempfile import mkstemp
from functions import *
django_header()
from moviemaker.models import *
import moviemaker.settings as mms 
FLVTOOLPP_PATH = "/home/pawel/bin/flvtool++"
FLVTOOLPP_OPTS = "-strip"

if __name__=="__main__":
    for movie in MovieCacheFile.objects.select_related():
        org_path = os.path.abspath(\
            os.path.join(mms.MOVIE_CACHE_DIR,movie.camera.cache_dir,movie.path)\
        )
        (fd,tmp_path) =  mkstemp() 
        retcode =  call([FLVTOOLPP_PATH, FLVTOOLPP_OPTS, org_path, tmp_path])
        if retcode > 0:
            print "ERROR while processing %s"%org_path
        else:
            shutil.move(tmp_path,org_path)
            call([mms.FLVTOOL2_PATH, "-U", org_path])
        

