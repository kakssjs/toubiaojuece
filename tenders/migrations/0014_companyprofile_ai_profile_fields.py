from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('tenders', '0013_historicalbidcase')]
    operations = [
        migrations.AddField(model_name='companyprofile', name='industry', field=models.CharField(blank=True, max_length=120, verbose_name='所属行业')),
        migrations.AddField(model_name='companyprofile', name='registered_capital', field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='注册资金')),
        migrations.AddField(model_name='companyprofile', name='employee_scale', field=models.CharField(blank=True, max_length=80, verbose_name='人员规模')),
        migrations.AddField(model_name='companyprofile', name='capability_tags', field=models.CharField(blank=True, max_length=500, verbose_name='企业能力标签')),
    ]
