# Generated manually

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('multilevel', '0001_initial'),  # Replace with actual latest migration
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(choices=[('writing', 'Writing'), ('speaking', 'Speaking')], max_length=20)),
                ('question_number', models.PositiveSmallIntegerField()),
                ('file', models.FileField(upload_to='submissions/%Y/%m/%d/')),
                ('file_type', models.CharField(choices=[('image', 'Image'), ('audio', 'Audio')], default='image', max_length=10)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('test_result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='multilevel.testresult')),
            ],
            options={
                'verbose_name': 'Submission Media',
                'verbose_name_plural': 'Submission Media',
                'ordering': ['section', 'question_number', 'uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='ManualReview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(choices=[('writing', 'Writing'), ('speaking', 'Speaking')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('reviewing', 'Reviewing'), ('checked', 'Checked')], default='pending', max_length=20)),
                ('total_score', models.FloatField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to=settings.AUTH_USER_MODEL)),
                ('test_result', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='manual_review', to='multilevel.testresult')),
            ],
            options={
                'verbose_name': 'Manual Review',
                'verbose_name_plural': 'Manual Reviews',
                'ordering': ['-created_at'],
                'unique_together': {('test_result', 'section')},
            },
        ),
        migrations.CreateModel(
            name='QuestionScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_number', models.PositiveSmallIntegerField()),
                ('score', models.FloatField()),
                ('comment', models.TextField(blank=True)),
                ('manual_review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_scores', to='multilevel.manualreview')),
            ],
            options={
                'verbose_name': 'Question Score',
                'verbose_name_plural': 'Question Scores',
                'ordering': ['question_number'],
                'unique_together': {('manual_review', 'question_number')},
            },
        ),
        migrations.CreateModel(
            name='ReviewLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('question_number', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('old_score', models.FloatField(blank=True, null=True)),
                ('new_score', models.FloatField(blank=True, null=True)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('manual_review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='multilevel.manualreview')),
                ('reviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Review Log',
                'verbose_name_plural': 'Review Logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
