#!/usr/bin/env python
import sys
import os
import re
import pytz

from datetime import datetime as dt
from shutil import move

dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir,'../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from moviemaker.models import *

REGEXP_TYPES = {'11_1111_111111.jpg' : "%y_%m%d_%H%M%S.jpg",
        'motion-2000-01-01-01-00-12.jpg' : "motion-%Y-%m-%d-%H-%M-%S.jpg" 
}

def main():
    try:
        camera_name, old_tz, src_dir = sys.argv[1:]
    except ValueError:
        print "Usage: %s <camera name> <old time zone> <src dir>"%sys.argv[0]
        exit(1)

    try:
        cam = Camera.objects.select_related().filter(name=camera_name).get()
        tz = pytz.timezone(old_tz)
        jpgs = os.listdir(src_dir) 
    except Camera.DoesNotExist:
        print "ERROR: Camera: %s not found."%camera_name
        exit(1)
    except pytz.UnknownTimeZoneError:
        print "ERROR: Incorrect time-zone string '%s'."%old_tz
        exit(1)
    except OSError:
        print "ERROR: %s is not a directory."%src_dir
        exit(1)

    fmt = ""
    for rev,rev_fmt in REGEXP_TYPES.items():
        try:
            re.match(cam.model.file2date_regexp,rev).groupdict()
            fmt = rev_fmt
            break
        except AttributeError:
            continue

    if not fmt:
        print "ERROR: No entry in REGEXP_TYPES for '%s'"\
                %cam.model.file2date_regexp

    for file in jpgs:
        try:
            date_d = re.match(cam.model.file2date_regexp,file).groupdict()
        except AttributeError:
            continue

        if int(date_d['year']) < 100:
            date_d['year'] = int(date_d['year'])+2000

        new_date = tz.localize(dt(int(date_d['year']),
            int(date_d['month']),
            int(date_d['day']),
            int(date_d['hour']),
            int(date_d['min']),
            int(date_d['sec']))).astimezone(pytz.timezone('UTC'))
        
        old_path = os.path.abspath(os.path.join(src_dir,file))
        new_path = os.path.abspath(
                    os.path.join(cam.home_dir,new_date.strftime(fmt))
                )
        move(old_path,new_path)
        print "Moved %s to  %s."%(old_path,new_path)

if __name__ == "__main__":
    main()
