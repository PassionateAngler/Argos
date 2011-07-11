from django.db.models.loading import AppCache
cache = AppCache()

for app in cache.get_apps():
    __import__(app.__name__)
    reload(app)

from django.utils.datastructures import SortedDict
cache.app_store = SortedDict()
cache.app_models = SortedDict()
cache.app_errors = {}
cache.handled = {}
cache.loaded = False

