import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    file_path = os.path.join(settings.BASE_DIR / 'data/ingredients.csv')

    def handle(self, *args, **options):
        args = list(args)
        if args:
            self.file_path = args[0]

        try:
            self._import_data()
        except Exception as err:
            self.stdout.write(self.style.ERROR(f'Ошибка при импорте: {err}'))
        else:
            self.stdout.write(self.style.SUCCESS('Данные загружены!'))

    def _import_data(self, file_name=file_path, encoding='UTF-8'):
        with open(file_name, encoding=encoding) as f:
            read_data = csv.reader(f)
            next(read_data)
            ingredients = [
                Ingredient(
                    name=name,
                    measurement_unit=measurement_unit
                )
                for name, measurement_unit in read_data
            ]

            Ingredient.objects.bulk_create(ingredients)
