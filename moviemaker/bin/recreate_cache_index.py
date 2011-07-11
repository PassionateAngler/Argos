#!/usr/bin/env python
from functions import *
django_header()
from moviemaker.models import *

if __name__=="__main__":
    if flvtool2_exsists() < 0 or moviecachedir_exists() < 0:
        sys.exit(2)
    for c in Camera.objects.all():
        recreate_camera_index(c)
