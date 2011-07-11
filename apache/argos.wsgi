import os, sys

apache_configuration= os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace) 

sys.path.append('/usr/lib/python2.5/site-packages/django/')
sys.path.append('/home/argos/argos/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'argos.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
