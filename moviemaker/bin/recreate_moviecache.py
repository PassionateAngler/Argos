#!/usr/bin/env python
from functions import *
django_header()
from moviemaker.models import *

if __name__=="__main__":
    (flvtool2_exsists() or mencoder_exists() or moviecachedir_exists())\
            and sys.exit(2)
    recreate_all()
    print "Recareting moviecache files. DONE."
    print "Reslicing moviecache files info..."
    for m in MovieCacheFile.objects.all():
        m.reslice()
