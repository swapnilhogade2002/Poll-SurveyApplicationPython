# Generated by Django 5.0.6 on 2024-07-10 06:18

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey_admin', '0010_answer_rating_answer'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateSurveyLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('respondent_email', models.EmailField(max_length=254)),
                ('link_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='private_links', to='survey_admin.survey')),
            ],
        ),
        migrations.CreateModel(
            name='PublicSurveyLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('survey', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='public_link', to='survey_admin.survey')),
            ],
        ),
    ]