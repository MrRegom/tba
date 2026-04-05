import os
import sys
import django

# Setup django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User, Group

def fix():
    try:
        u = User.objects.get(username='profesor')
        g = Group.objects.get(name='profesor')
        u.groups.add(g)
        u.save()
        print(f"DEBUG: User {u.username} (pk={u.pk}) now has groups: {[gr.name for gr in u.groups.all()]}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    fix()
