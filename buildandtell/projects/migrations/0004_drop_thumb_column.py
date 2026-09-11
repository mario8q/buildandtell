from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_buildupdate_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE projects_project DROP COLUMN thumb;',
            reverse_sql="ALTER TABLE projects_project ADD COLUMN thumb varchar(100) NOT NULL DEFAULT '';",
        ),
    ]