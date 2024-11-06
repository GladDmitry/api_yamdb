import csv

from django.core.management.base import BaseCommand, CommandError
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import UserProfile


CSV_PATH = 'static/data/'

FOREIGN_KEY_FIELDS = ('category', 'author')

DICT = {
    UserProfile: 'users.csv',
    Genre: 'genre.csv',
    Category: 'category.csv',
    Title: 'titles.csv',
    Review: 'review.csv',
    Comment: 'comments.csv'
}


class Command(BaseCommand):
    help = 'Загрузка данных из файла формата csv в базу данных.'

    def csv_serializer(self, csv_data, model):
        objs = []
        for row in csv_data:
            for field in FOREIGN_KEY_FIELDS:
                if field in row:
                    row[f'{field}_id'] = row[field]
                    del row[field]
            objs.append(model(**row))
        model.objects.bulk_create(objs)

    def load_csv(self, model):
        try:
            with open(
                CSV_PATH + DICT[model],
                newline='',
                encoding='utf8'
            ) as csv_file:
                self.csv_serializer(csv.DictReader(csv_file), model)
            self.stdout.write(self.style.SUCCESS(
                f'Файл {model} успешно загружен.'))
        except Exception as error:
            CommandError(error)
        self.stdout.write(
            self.style.SUCCESS(
                f"Данные из файла {DICT[model]} успешно занесены в БД"
            )
        )

    def handle(self, *args, **kwargs):
        for model in DICT:
            self.load_csv(model)
        self.stdout.write(self.style.SUCCESS(
            'Все файлы успешно загружены в базу данных.'))
