#!/usr/bin/env python
import sys
import os
import re
import subprocess
from datetime import datetime as dt
import pytz
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir,'../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from moviemaker.models import *

def imagefiles_insert_sql_query(cameras):
    query_string = r"""INSERT INTO moviemaker_imagefile
    (camera_id,path,_date) VALUES %s;"""
    values_list = [] 
    for camera in cameras:
        try:
            for img in os.listdir(camera.home_dir):
                img_path = os.path.join(camera.home_dir,img)
                #do not put image into db if it is empty
                if os.path.getsize(img_path) < ImageFile.MIN_SIZE:
                    print "ERROR:%s has %d bytes. Skiping..."%(img_path,\
                            os.path.getsize(img_path))
                    continue
                m = re.match(camera.model.file2date_regexp,img)
                try:
                    year = int(m.group('year'))
                    if year < 2000:
                        year += 2000
                    file_time = dt(
                            year,int(m.group('month')),int(m.group('day')),
                            int(m.group('hour')),int(m.group('min')),
                            int(m.group('sec')),tzinfo=pytz.timezone('UTC')
                            ).strftime("%Y-%m-%d %H:%M:%S%z")
                    values_list.append(r"(%d,'%s','%s')"%(camera.id,img_path,file_time))                  
                except AttributeError:
                    pass
        except OSError, (errno, strerror):
            print strerror
            print "Directory %s does not exist."%camera.home_dir
    return query_string%",".join(values_list)


def main():
    from django.db import connection, transaction
    from django.conf import settings

    cameras = Camera.objects.all()
    ImageFile.objects.all().delete()
    sql =  imagefiles_insert_sql_query(cameras)
    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit_unless_managed()

if __name__ == "__main__":
    main()
