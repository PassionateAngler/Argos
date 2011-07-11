#!/usr/bin/env python
import os
import shutil
from functions import django_header, create_tmpdir
django_header()
from moviemaker.settings import MOVIE_MIN_LENGTH
from moviemaker.models import Camera
from django.db.models import Max

if __name__=="__main__":
    cams = Camera.objects.filter(moviecachefile__duration__gt = MOVIE_MIN_LENGTH)\
        .annotate(max_end = Max('moviecachefile___end'))
    try:
        tempdir = create_tmpdir()
        for cam in cams:
            ifiles = cam.imagefile_set.filter(_date__gt=cam.max_end)
            cam.update_moviecache(ifiles, tempdir, MOVIE_MIN_LENGTH)
    finally:
        if os.path.isdir(tempdir):
            shutil.rmtree(tempdir)



