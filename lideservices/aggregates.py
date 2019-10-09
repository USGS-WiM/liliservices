from django.db.models import Aggregate


class Median(Aggregate):
    name = 'Median'
    function = 'MEDIAN'

