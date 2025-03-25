import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('multilevel', '0012_remove_usertest_result_remove_usertest_test_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='section',
            options={'verbose_name': "Bo'lim", 'verbose_name_plural': "Bo'limlar"},
        ),
        migrations.AlterModelOptions(
            name='test',
            options={'verbose_name': 'Test', 'verbose_name_plural': 'Testlar'},
        ),
        migrations.RemoveField(
            model_name='section',
            name='submitters',
        ),
        migrations.RemoveField(
            model_name='test',
            name='options',
        ),
        migrations.AlterField(
            model_name='option',
            name='text',
            field=models.CharField(max_length=255, verbose_name='Variant'),
        ),
        migrations.AlterField(
            model_name='section',
            name='duration',
            field=models.PositiveSmallIntegerField(default=5, verbose_name='Test vaqti (daqiqa)'),
        ),
        migrations.AlterField(
            model_name='section',
            name='level',
            field=models.CharField(choices=[('a1', 'A1'), ('a2', 'A2'), ('b1', 'B1'), ('b2', 'B2'), ('c1', 'C1'), ('multilevel', 'Multilevel')], default='multilevel', max_length=20, verbose_name='Daraja'),
        ),
        migrations.AlterField(
            model_name='section',
            name='type',
            field=models.CharField(choices=[('listening', 'Listening'), ('reading', 'Reading'), ('writing', 'Writing'), ('speaking', 'Speaking')], max_length=20, verbose_name="Bo'lim turi"),
        ),
        migrations.AlterField(
            model_name='test',
            name='options_array',
            field=models.TextField(blank=True, null=True, verbose_name='Variantlar JSON'),
        ),
        migrations.AlterField(
            model_name='test',
            name='order',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Tartib raqami'),
        ),
        migrations.AlterField(
            model_name='test',
            name='section',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='multilevel.section', verbose_name="Bo'lim"),  # default=1 qo‘yildi
        ),
        migrations.AlterField(
            model_name='testresult',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Tugash vaqti'),
        ),
        migrations.AlterField(
            model_name='testresult',
            name='section',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='multilevel.section', verbose_name="Bo'lim"),  # default=1 qo‘yildi
        ),
        migrations.AlterField(
            model_name='testresult',
            name='start_time',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Boshlanish vaqti'),
        ),
        migrations.AlterField(
            model_name='testresult',
            name='status',
            field=models.CharField(choices=[('started', 'Boshlangan'), ('completed', 'Yakunlangan')], default='started', max_length=20, verbose_name='Holati'),
        ),
        migrations.AlterField(
            model_name='useranswer',
            name='is_correct',
            field=models.BooleanField(default=False, verbose_name='To‘g‘ri javob'),
        ),
        migrations.AlterField(
            model_name='usertest',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Kutilmoqda'), ('paid', 'To‘langan')], default='pending', max_length=20, verbose_name='To‘lov holati'),
        ),
        migrations.AlterField(
            model_name='usertest',
            name='score',
            field=models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Natija'),
        ),
        migrations.AlterField(
            model_name='usertest',
            name='status',
            field=models.CharField(choices=[('created', 'Yaratildi'), ('started', 'Boshlangan'), ('completed', 'Yakunlangan')], default='created', max_length=20, verbose_name='Holati'),
        ),
    ]