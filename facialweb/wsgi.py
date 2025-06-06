import os
import sys

# Añade la ruta de tu proyecto Django
path = '/home/natasaur/facialweb_PA/facialweb'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'facialweb.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
