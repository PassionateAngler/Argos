import re
import datetime
from django.db import models
from timezones.fields import *
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError
from django.forms import ModelForm

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
    str
class Camera(models.Model):
    localization = models.ForeignKey(Localization)
    model = models.ForeignKey(CameraModel)
    name = models.CharField(max_length=200,unique=True)
    slug = models.SlugField(max_length=200,unique=True, 
        validators=[validate_slug]) 
    home_dir = models.FilePathField(unique=True)
    cache_dir = models.FilePathField(unique=True)
    def __unicode__(self):
        return self.name

class ImageFile(models.Model):
    camera = models.ForeignKey(Camera)
    path = models.FilePathField(max_length=500,unique=True,db_index=True)
    date = LocalizedDateTimeField(db_index=True,\
            default=datetime.datetime(1970,1,1),timezone='UTC')
    def __unicode__(self):
        return '%s %s' % (self.date.strftime('%Y-%m-%d %H:%M:%S %Z%z') , self.path )

class MovieCacheFile(models.Model):
    camera = models.ForeignKey(Camera)
    path = models.FilePathField(db_index=True, default='')
    duration = models.IntegerField(default=0)
    frames_desc = models.TextField(default='[]')
    start = LocalizedDateTimeField(db_index=True,\
            default=datetime.datetime(1970,1,1),timezone='UTC')
    end = LocalizedDateTimeField(db_index=True,\
            default=datetime.datetime(1970,1,1),timezone='UTC')
    def __unicode__(self):
        return '%s - %s: %s' % (self.start.strftime('%Y-%m-%d %H:%M:%S %Z%z'),\
        self.end.strftime('%Y-%m-%d %H:%M:%S %Z%z'), self.path )

