from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Resets the primary key sequence for a model to max(id)+1'

    def add_arguments(self, parser):
        parser.add_argument('model', type=str, help='The model name in app.Model format')

    def handle(self, *args, **options):
        try:
            from django.apps import apps
            model = apps.get_model(options['model'])
            reset_primary_key_sequence(model)
            self.stdout.write(self.style.SUCCESS(f'Successfully reset sequence for {options["model"]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))


def reset_primary_key_sequence(model):
    """Reset the primary key sequence for a model, skipping existing IDs"""
    table_name = model._meta.db_table
    with connection.cursor() as cursor:
        # Get the current maximum ID
        cursor.execute(f"SELECT MAX(id) FROM {table_name};")
        max_id = cursor.fetchone()[0] or 0

        # Reset the sequence to start after the highest existing ID
        cursor.execute(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH {max_id + 1};")

# terminal command -> python manage.py reset_id_sequence accounts.HouseManagerUser /app.model name/