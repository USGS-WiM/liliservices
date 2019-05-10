from django.db.models import Aggregate


class Median(Aggregate):
    name = 'Median'
    function = 'MEDIAN'

    def convert_value(self, value, expression, connection, context):
        return value
