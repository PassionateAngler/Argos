#!/usr/bin/env python
from functions import django_header
django_header()
from moviemaker.models import Camera

if __name__=="__main__":
    for cam in Camera.objects.all():
        print "Adding new files..."
        cam.add_imagefiles()


