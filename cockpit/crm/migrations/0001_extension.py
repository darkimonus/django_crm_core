from django.db import migrations
from django.contrib.postgres.operations import BtreeGistExtension


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        BtreeGistExtension(),
    ]
