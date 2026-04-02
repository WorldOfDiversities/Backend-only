#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    # Render may invoke "python manage.py runserver" without an explicit bind.
    # Ensure it still listens on the required external interface/port.
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        has_bind_arg = any(
            (':' in arg) or (arg in {'0.0.0.0', '127.0.0.1', 'localhost'})
            for arg in sys.argv[2:]
        )
        render_port = os.getenv('PORT', '').strip()
        if render_port and not has_bind_arg:
            sys.argv.append(f'0.0.0.0:{render_port}')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
