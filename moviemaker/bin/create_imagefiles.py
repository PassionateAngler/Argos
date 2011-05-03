#!/usr/bin/env python
import sys
import os
import re
from datetime import datetime as dt
import pytz
dir = os.path.dirname(__file__)
sys.path.append(os.path.join(dir,'../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from moviemaker.models import *

def imagefiles_insert_sql_query(cameras):
    query_string = r"""INSERT INTO moviemaker_imagefile
    (camera_id,path,date) VALUES %s;"""
    values_list = [] 
    for camera in cameras:
        try:
            for img in os.listdir(camera.home_dir):
                img_path = camera.home_dir+'/'+img
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
        except OSError:
            print "Directory %s does not exist."%camera.home_dir
    return query_string%",".join(values_list)


def main():
    from django.db import connection, transaction
    from django.conf import settings

    cameras = Camera.objects.all()
    sql =  imagefiles_insert_sql_query(cameras)
    cursor = connection.cursor()
    cursor.execute(sql)
    transaction.commit_unless_managed()

if __name__ == "__main__":
    main()
