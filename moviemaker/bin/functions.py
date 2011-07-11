import sys
import os
import subprocess
import re
import pytz
import yaml
import tempfile
from datetime import datetime as dt

def django_header():
    dir = os.path.dirname(__file__)
    sys.path.append(os.path.join(dir,'../../'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

django_header()
from django.db import connection, transaction
from moviemaker.settings import *
from moviemaker.models import *

def create_tmpdir():
    if os.path.isdir('/dev/shm'):
        tempdir = tempfile.mkdtemp(dir='/dev/shm')
    else:
        tempdir = tempfile.mkdtemp()
    return tempdir

def clear_dir(directory):
    if os.listdir(directory):
        try:
            subprocess.call([r"rm -r %s/*"%directory],shell=True)
        except OSError, e:
            MEDIA_LOGGER.error(e)

def flvtool2_exsists():
    #TODO
    #add checking does FLVTOOL2_PATH is realy pointing to flvtool2 binary
    try:
        subprocess.call([FLVTOOL2_PATH],stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return 0
    except OSError:
        MEDIA_LOGGER.error("Incorrect movimaker.settings.FLVTOOL2_PATH")
        return -1

def mencoder_exists():
    #TODO
    #add checking does  MENCODER_PATH is realy pointing to mencoder binary
    try:
        subprocess.call([MENCODER_PATH],stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        MEDIA_LOGGER.error("Incorrect movimaker.settings.MENCODER_PATH")
        return -1

def moviecachedir_exists():
    if not os.path.isdir(MOVIE_CACHE_DIR):
        MEDIA_LOGGER.error(\
            "Directory: %s does not exists.\nPlease create it and make writable."\
            %os.path.abspath(MOVIE_CACHE_DIR)\
        )
        return -1
    else:
        return 0

#MOVIE INDEX FUNCTIONS

#recreate MovieCacheFiles (from existing video files) of Camera 
def recreate_camera_index(camera):
    cam_path = os.path.abspath(os.path.join(MOVIE_CACHE_DIR,camera.cache_dir))
    MEDIA_LOGGER.info(\
        "Re-creating index for %s from directory:\n%s"\
        %(camera.name,cam_path)\
    )
    if not os.path.isdir(cam_path):
        MEDIA_LOGGER.error(\
            "cache directory:\n%s does not exists.\nSkiping."\
            %cam_path\
        )
        sys.exit(2)
    
    camera.moviecachefile_set.all().delete()

    m_int = lambda match,key: int(match.group(key))

    for movie_name in os.listdir(cam_path):
        m = re.match(MOVIE_NAME_REGEXP,movie_name,re.X) 
        if m:
            start = \
                dt(m_int(m,'year_s'),m_int(m,'month_s'),m_int(m,'day_s'),\
                m_int(m,'h_s'),m_int(m,'m_s'),m_int(m,'s_s')) 
            end = \
                dt(m_int(m,'year_e'),m_int(m,'month_e'),m_int(m,'day_e'),\
                m_int(m,'h_e'),m_int(m,'m_e'),m_int(m,'s_e')) 
            duration = m_int(m,'duration')

            frames =\
                camera.imagefile_set.filter(_date__range=(start,end))\
                .order_by('_date')
            if not frames:
                MEDIA_LOGGER.error(\
                    "No images for movie %s. Skiping..."\
                    %movie_name\
                )
                continue

            recreate_movie_index(camera, movie_name, frames,\
                    time_info=(start,end,duration))
        else:
            MEDIA_LOGGER.error("%s is not a movie file."%movie_name)

#MOVIE FILES FUNCTIONS
#[re]create MovieCacheFile entry and add Keyframes from .flv file
def recreate_movie_index(camera, movie_name, frames, time_info):
    MEDIA_LOGGER.info("re-creating index for %s"%movie_name)

    (start,end,duration) = time_info

    if not (start and end and duration):
        MEDIA_LOGGER.error("ERROR incorrect time_info tuple")
        return -1
    
    cam_path = os.path.abspath(os.path.join(MOVIE_CACHE_DIR,camera.cache_dir))
    movie_path = os.path.abspath(os.path.join(cam_path,movie_name))

    flvtool_ps =\
    subprocess.Popen(\
        [FLVTOOL2_PATH,"-UP",movie_path],\
        stdout=subprocess.PIPE,\
        stderr=subprocess.STDOUT\
    )

    (flvtool_out,flvtool_err) = flvtool_ps.communicate()
    if flvtool_out.find("ERROR") >= 0:
        MEDIA_LOGGER.error("FLVTOOL2 ERROR while processing %s:\n%s"\
            %(movie_name,"\n".join([str(flvtool_out),str(flvtool_err)])))
        return -1
    
    keyframes = yaml.load(flvtool_out).get(movie_path).get('keyframes')
    
    if not (keyframes and keyframes.get('times')):
        MEDIA_LOGGER.warning("Wrong flv format. Skiping")
        return -1

    keyframes = map(lambda k: int(k),keyframes.get('times'))
    mc =\
    camera.moviecachefile_set.create(path=movie_name,duration=duration,_start=start,_end=end)
    sql = "INSERT INTO moviemaker_keyframe\
    (imagefile_id,moviecachefile_id,slice_id,position) VALUES %s;"
    values_sql = []
    for kf in keyframes:
        values_sql.append(r"(%d,%d,-1,%d)"%(frames[kf].id,mc.id,kf))
    sql = sql%",".join(values_sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit_unless_managed()
    return mc

#create movie
#@return int or MovieCacheFile 
def create_movie(camera,frames,tempdir):
    import subprocess as process
    date2strfmt = "%Y%m%d_%H%M%S"
    start = frames[0].date
    duration = len(frames)
    end = frames[len(frames)-1].date
    filename = "%s_%d_%s_%s.flv"%(start.strftime(date2strfmt),\
            duration, end.strftime(date2strfmt), camera.name)
    
    #Create and write temprorary file for mencoder
    (fd,path) = tempfile.mkstemp(dir=tempdir)
    tmpfile = os.fdopen(fd,'w')
    tmpfile.write("\n".join(map(lambda img:img.path,frames)))
    tmpfile.flush()
    tmpfile.close()
    output = os.path.join(MOVIE_CACHE_DIR,camera.cache_dir,filename)
    MEDIA_LOGGER.info("Creating file: %s"%filename)
    #RUN MENCODER
    MEDIA_LOGGER.debug(MENCODER_CMD(path,output))
    return_value = subprocess.call(MENCODER_CMD(path,output).split())
    #RUN FLVTOOL and insert information about movie into database
    ti = (start,end,duration)
    mc = return_value or recreate_movie_index(camera, filename, frames, ti)
    if mc.__class__ == MovieCacheFile:
        mc.reslice()
    #clear everything for another movie
    os.remove(path)
    return mc

#recreate ALL MovieCacheFiles of Camera 
def recreate_camera_cache(camera,tempdir):
    MovieCacheFile.objects.filter(camera=camera).delete()
    ifiles = camera.imagefile_set.order_by('_date')
    camera.update_moviecache(ifiles,tempdir)
    
#recreate
def recreate(camera):
    import shutil
    import traceback

    if os.path.isdir(os.path.join(MOVIE_CACHE_DIR,camera.cache_dir)):
        shutil.rmtree(os.path.join(MOVIE_CACHE_DIR,camera.cache_dir)) 
    
    tempdir = create_tmpdir()

    try:
        recreate_camera_cache(camera,tempdir)
    finally:
        shutil.rmtree(tempdir) 

#recreate_all
#TODO WTF!!! why program is not throwing 'no space left on device'???
def recreate_all():
    import shutil
    import traceback
    clear_dir(MOVIE_CACHE_DIR)
    MovieCacheFile.objects.all().delete()

    tempdir = create_tmpdir()
    try:
        for c in Camera.objects.all():
            recreate_camera_cache(c,tempdir)
    finally:
        shutil.rmtree(tempdir)         

