import re
import os
import shutil
import datetime
from django.db import models
from timezones.fields import *
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.forms import ModelForm
from moviemaker.bin.functions import create_movie, create_tmpdir
import moviemaker.settings as mms

def validate_regexp(pattern):
    try:
        re.compile(pattern)
    except:
        raise ValidationError(u'%s is not correct Python regular expression\
            pattern.' % pattern )

class Localization(models.Model):
    name = models.CharField(max_length=200,unique=True,)
    slug = models.SlugField(max_length=200,unique=True,
        validators=[validate_slug])  
    timezone = TimeZoneField()
    def __unicode__(self):
        return self.name

class CameraModel(models.Model):
    name = models.CharField(max_length=200,unique=True)
    slug = models.SlugField(max_length=200,unique=True, 
        validators=[validate_slug])  
    file2date_regexp = models.CharField(max_length=200, 
        validators=[validate_regexp]) 
    def __unicode__(self):
        return self.name

class Camera(models.Model):
    localization = models.ForeignKey(Localization)
    model = models.ForeignKey(CameraModel)
    name = models.CharField(max_length=200,unique=True)
    slug = models.SlugField(max_length=200,unique=True, 
        validators=[validate_slug]) 
    home_dir = models.FilePathField(unique=True)
    cache_dir = models.FilePathField(unique=True)

    #function adds ImageFile to this Camera 
    #if it is newest than oldest ImageFile in db
    def add_imagefiles(self):
        import os
        import re
        from datetime import datetime as dt
        imgs = [] 
        regexp = self.model.file2date_regexp
        last_date = self.imagefile_set.order_by('-_date')[0]._date
        last_added = None
        num_added = 0
        for img in os.listdir(self.home_dir):
            m = re.match(regexp, img) 
            if m:
                if int(m.group('year')) < 100:
                    year = int(m.group('year')) + 2000
                else:
                    year = int(m.group('year'))

                img_date = dt( 
                    year,
                    int(m.group('month')),
                    int(m.group('day')),
                    int(m.group('hour')),
                    int(m.group('min')),
                    int(m.group('sec'))
                )
                img_path = os.path.join(self.home_dir,img)

                #put to db only if image is larger than ImageFile.MIN_SIZE
                is_not_empty = os.path.getsize(img_path) > ImageFile.MIN_SIZE
                if is_not_empty and img_date > last_date :
                    last_added = self.imagefile_set.create(
                        _date = img_date,
                        path = img_path
                    )
                    num_added += 1
                else:
                    if not is_not_empty:
                        mms.MEDIA_LOGGER.error("ERROR:%s has %d bytes. Skiping..."%(img_path,\
                            os.path.getsize(img_path)))
            #ENDFOR
        #Log statistics of added files
        if last_added:
            mms.ARGOS_LOGGER.info(
                "Camera: %s added %d imagefiles, last added %s"%\
                (self.name,num_added,last_added.date)
            )

    #create MovieCacheFile from range start to end
    def create_moviecachefile(self, start, end):
        movie = None
        frames = ImageFile.objects.filter(\
            camera=self,\
            _date__range=(start,end)\
        )
        if frames.count() >= 3:
            try:
                tempdir = create_tmpdir()
                movie = create_movie(self,frames,tempdir)
                if not  movie.__class__ == MovieCacheFile:
                    movie = None
                    mms.MEDIA_LOGGER.error(\
                        "Creating movie cache file for range %s %s failed"\
                        %(start,end)
                    )
            finally:
                if os.path.isdir(tempdir):
                    shutil.rmtree(tempdir)
        else:
            mms.ARGOS_LOGGER.debug(\
                "Camera %s: no images for range %s to %s"\
                %(\
                    self.slug,\
                    start,\
                    end\
                )\
            )
        return movie

    #update this Camera`s MovieCacheFiles
    def update_moviecache(self, ifiles, tempdir, min_length = 0):
        cache_dir = os.path.join(mms.MOVIE_CACHE_DIR, self.cache_dir)
        if not os.path.isdir(cache_dir):
            os.mkdir(cache_dir)

        full_parts = len(ifiles)/mms.MOVIE_MAX_LENGHT
        offset = len(ifiles)%mms.MOVIE_MAX_LENGHT
        start = 0
    
        #full MOVIE_MAX_LENGHT movies
        for part in range(full_parts):
            start = part*mms.MOVIE_MAX_LENGHT
            create_movie(self, ifiles[start:start+mms.MOVIE_MAX_LENGHT],\
                    tempdir) 
        #offset movie
        if offset and offset > min_length:
            start = full_parts*mms.MOVIE_MAX_LENGHT
            create_movie(self, ifiles[start:start+offset], tempdir) 

    def __unicode__(self):
        return self.name

class ImageFile(models.Model):
    MIN_SIZE = 100
    camera = models.ForeignKey(Camera)
    path = models.FilePathField(max_length=500,unique=True,db_index=True)
    _date = models.DateTimeField(db_index=True,\
            default=datetime.datetime(1970,1,1))

    def set_date(self, s):
        if s.tzinfo:
            s = s.astimezone(pytz.timezone('UTC'))
        self._date = s
    def get_date(self):
        return pytz.timezone('UTC').localize(self._date)
    def date_localized(self):
        return self.date.astimezone(self.camera.localization.timezone)
    def __unicode__(self):
        return '%s %s' % (self.date.strftime('%Y-%m-%d %H:%M:%S %Z%z') , self.path )
    class Meta:
        ordering = ['_date']

    date = property(get_date,set_date)

class MovieCacheFile(models.Model):
    MAX_SLICE_DIST = 3600 #in secounds
    MIN_SLICE_FRAMES = 5 #in frames

    camera = models.ForeignKey(Camera)
    path = models.FilePathField(db_index=True, default='', unique=True)
    duration = models.IntegerField(default=0)
    key_frames = models.ManyToManyField(ImageFile, through='KeyFrame')
    _start = models.DateTimeField(db_index=True,\
            default=datetime.datetime(1970,1,1))
    _end = models.DateTimeField(db_index=True,\
            default=datetime.datetime(1970,1,1))

    def get_start(self):
        return pytz.timezone('UTC').localize(self._start)
    def set_start(self, s):
        if s.tzinfo:
            s = s.astimezone(pytz.timezone('UTC'))
        self._start = s
    def get_end(self):
        return pytz.timezone('UTC').localize(self._end)
    def set_end(self, s):
        if s.tzinfo:
            s = s.astimezone(pytz.timezone('UTC'))
        self._end = s
    start = property(get_start,set_start)
    end = property(get_end,set_end)

    def reslice(self,\
            max_slice_dist = MAX_SLICE_DIST,\
            min_slice_frames = MIN_SLICE_FRAMES):
        frames =\
            KeyFrame.objects.select_related().filter(moviecachefile=self).order_by('position')
        delta = datetime.timedelta(seconds=max_slice_dist)
        slice_id = 0
        for end,frame in enumerate(frames):
            if frame.position == 0:
                start_f = frame
            if frame.imagefile.date >= start_f.imagefile.date+delta or\
                    end == len(frames)-1: 
            #start new slice
                KeyFrame.objects.filter(moviecachefile=self\
                        ,position__range=(start_f.position,end))\
                        .update(slice_id=slice_id)
                start_f = frame
                slice_id+=1

    def slices(self):
        slices = []
        prev = -1
        for (idx,f) in\
        enumerate(KeyFrame.objects.select_related().filter(moviecachefile=self).order_by('position')):
            if f.slice_id != prev:
                prev = f.slice_id
                slices.append({'first':f,'last':f,'slices':[]})
            slices[f.slice_id]['last'] = f
            slices[f.slice_id]['slices'].append(f)
        return slices

    def create_subs_tt(self, s_time = None, e_time = None):
        from xml.dom.minidom import Document
        timezone = self.camera.localization.timezone
        subtitles = Document()
        tt = subtitles.createElement('tt')
        tt.setAttribute("xml:lang","en") 
        tt.setAttribute("xmlns","http://www.w3.org/2006/10/ttaf1") 
        tt.setAttribute("xmlns:tts","http://www.w3.org/2006/10/ttaf1#styling") 
        tt.setAttribute("xmlns:tts","http://www.w3.org/2006/10/ttaf1#styling") 
        subtitles.appendChild(tt)

        head = subtitles.createElement('head')
        tt.appendChild(head)
        styling = subtitles.createElement('styling')
        
        body = subtitles.createElement('body')
        tt.appendChild(body)
        div = subtitles.createElement('div')
        div.setAttribute("xml:lang","en")
        body.appendChild(div)

        #select which keyframes will be used for creating subtitles
        keyframes = self.keyframe_set.select_related()
        if s_time != None and e_time != None:
            keyframes = keyframes.filter(position__gte=s_time,position__lte=e_time)

        for (position,frame) in enumerate(keyframes):
            p = subtitles.createElement('p')
            p.setAttribute("begin","%ss"%position)
            p.setAttribute("dur","01:00")
            p.appendChild(subtitles.createTextNode("%s"%frame.imagefile.date.astimezone(timezone)))
            div.appendChild(p)

        return subtitles.toprettyxml()

    def __unicode__(self):
        return '%s - %s: %s' % (self.start.strftime('%Y-%m-%d %H:%M:%S %Z%z'),\
        self.end.strftime('%Y-%m-%d %H:%M:%S %Z%z'), self.path )
    class Meta:
        ordering = ['_start']

class KeyFrame(models.Model):
    imagefile = models.ForeignKey(ImageFile)
    moviecachefile = models.ForeignKey(MovieCacheFile)
    position = models.IntegerField(default=0,db_index=True)
    slice_id = models.IntegerField(default=-1,db_index=True)

    def __unicode__(self):
        return str(self.slice_id)+":"+str(self.position)

    class Meta:
        ordering = ['position']

