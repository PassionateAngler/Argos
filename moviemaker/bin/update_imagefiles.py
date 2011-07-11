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

def main():
    for camera in Camera.objects.select_related():
        camera.add_imagefiles()

if __name__ == "__main__":
    main()
