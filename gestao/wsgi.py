"""
WSGI config for gestao project.
"""
import os
from django.core.wsgi import get_wsgi_application

# Força o uso do SQLite no servidor do PythonAnywhere
os.environ['USE_SQLITE'] = 'True'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestao.settings')

application = get_wsgi_application()