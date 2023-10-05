import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла'

    file_path = os.path.join(settings.BASE_DIR, 'data/ingredients.csv')

    def add_arguments(self, parser):
        parser.add_argument('file_path',
                            nargs='?',
                            type=str,
                            help='Путь к CSV файлу')

    def handle(self, *args, **options):
        file_path = options.get('file_path')

        try:
            self._import_data(file_path)
        except Exception as err:
            self.stdout.write(self.style.ERROR(f'Ошибка при импорте: {err}'))
        else:
            self.stdout.write(self.style.SUCCESS('Данные загружены!'))

    def _import_data(self, file_name=file_path, encoding='UTF-8'):
        with open(file_name, encoding=encoding) as file:
            read_data = csv.reader(file)
            next(read_data)
            ingredients = [
                Ingredient(
                    name=name,
                    measurement_unit=measurement_unit
                )
                for name, measurement_unit in read_data
            ]

            Ingredient.objects.bulk_create(ingredients)
