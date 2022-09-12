import os
import datetime
from django.conf import settings

date = datetime.datetime.now()
filename_secrets_bx24 = os.path.join(settings.BASE_DIR, 'reports', 'report.txt')


class Report:
    def __init__(self):
        self.filename = None

    def create(self):
        self.forming_filename()
        with open(self.filename, 'a+'):
            pass

    def add_row(self, row):
        print("+" * 88)
        with open(self.filename, 'a') as f:
            f.write(row + "\n")

    def forming_filename(self):
        date_str = self.get_date_now_str()
        self.filename = os.path.join(settings.BASE_DIR, 'reports', f'report_{date_str}.txt')

    def get_date_now_str(self):
        date_actual = datetime.datetime.now()
        return date_actual.strftime("%d.%m.%Y_%H.%M")







