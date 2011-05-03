#!/usr/bin/env python
import sys
import os
import subprocess
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir,'../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from moviemaker import settings as mms

#TODO
#add checking does  MENCODER_PATH is realy pointing to mencoder binary
try:
    subprocess.call([mms.MENCODER_PATH],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except OSError:
    print "Incorrect movimaker.settings.MENCODER_PATH"
    sys.exit(2)

#TODO
#add checking does FLVTOOL2_PATH is realy pointing to flvtool2 binary
try:
    subprocess.call([mms.FLVTOOL2_PATH],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except OSError:
    print "Incorrect movimaker.settings.FLVTOOL2_PATH"

if not os.path.isdir(mms.MOVIE_CACHE_DIR):
    print "Directory: %s does not exists. Please create it and make\
    writable."%mms.MOVIE_CACHE_DIR
    sys.exit(2)

import re
import pytz
import tempfile 
from datetime import datetime as dt
from django.db import connection, transaction
from moviemaker.models import *

run_mencoder = lambda src,dst:"%s \
mf://@%s \
-mf fps=1:type=jpg \
-ovc lavc \
-of lavf \
-lavcopts %s \
-quiet \
-o %s"%(mms.MENCODER_PATH, src, mms.MENCODER_LAVCOPTS, dst)

#print run_mencoder('cam94-5','test.flv')
#sys.exit(0)

def clear_dir(directory):
    if os.listdir(directory):
        try:
            subprocess.call([r"rm -r %s/*"%directory],shell=True)
        except OSError, e:
            print(e)
            #print "Can not delete all files from %s"%directory 

#create movie
def create_movie(camera,frames,tempdir):
    #import pprint
    import subprocess as process
    import simplejson as json
    date2strfmt = "%Y%m%d_%H%M%S"
    filename = "%s_%d_%s_%s.flv"%(frames[0].date.strftime(date2strfmt),\
            len(frames), frames[-1].date.strftime(date2strfmt), camera.name)
    desc = json.dumps(map(lambda frame:\
            frame.date\
            .astimezone(camera.localization.timezone)\
            .strftime('%Y-%m-%d %H:%M:%S %z %Z'),\
            frames))
    #print "\n".join(json.loads(desc))
    
    #Create and write temprorary file for mencoder
    (fd,path) = tempfile.mkstemp(dir=tempdir)
    tmpfile = os.fdopen(fd,'w')
    tmpfile.write("\n".join(map(lambda img:img.path,frames)))
    tmpfile.flush()
    tmpfile.close()
    #RUN MENCODER
    filename = os.path.join(mms.MOVIE_CACHE_DIR,camera.cache_dir,filename)
    print "Creating file: %s"%filename
    mencoder_return = subprocess.call([run_mencoder(path,filename)],shell=True)
    #insert information about movie into database
    camera.moviecachefile_set.create(path=filename,\
            start=frames[0].date,\
            end=frames[-1].date,\
            duration=len(frames),\
            frames_desc=desc)
    camera.save()
    #clear everything for another movie
    os.remove(path)

#recreate camera cache
def recreate_camera(camera,tempdir):
    os.mkdir(os.path.join(mms.MOVIE_CACHE_DIR,camera.cache_dir))
    ifiles = camera.imagefile_set.all().order_by('date')

    full_parts = len(ifiles)/mms.MOVIE_MAX_LENGHT
    offset = len(ifiles)%mms.MOVIE_MAX_LENGHT
    start = 0

    #full mms.MOVIE_MAX_LENGHT movies
    for part in range(full_parts):
        start = part*mms.MOVIE_MAX_LENGHT
        create_movie(camera, ifiles[start:start+mms.MOVIE_MAX_LENGHT],\
                tempdir) 
    #offset movie
    if offset:
        start = full_parts*mms.MOVIE_MAX_LENGHT
        create_movie(camera, ifiles[start:start+offset], tempdir) 

#recreate
#TODO WTF!!! why program is not throwing 'no space left on device'???
def recreate():
    import shutil
    import traceback
    clear_dir(mms.MOVIE_CACHE_DIR)
    MovieCacheFile.objects.all().delete()

    if os.path.isdir('/dev/shm'):
        tempdir = tempfile.mkdtemp(dir='/dev/shm')
    else:
        tempdir = tempfile.mkdtemp()

    try:
        for c in Camera.objects.all():
            recreate_camera(c,tempdir)
    finally:
        shutil.rmtree(tempdir)         

if __name__=="__main__":
    print mms.MOVIE_CACHE_DIR
    recreate()
    #c = Camera.objects.all()[0]
    #recreate_camera(c)
