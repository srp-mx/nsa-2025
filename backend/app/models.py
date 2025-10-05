"""
Models for the app.

This file defines the database models for the application system.
"""
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.gis.db import models as gis_models

# Create your models here.

class Organization(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

class Site(models.Model):
    region = gis_models.PolygonField(srid=4326)
    organization = models.ForeignKey(
            Organization,
            on_delete=models.CASCADE,
            related_name="sites",
            db_index=True
    )

class Auditor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

class Audit(models.Model):
    score = models.IntegerField()
    max_score = models.IntegerField()
    is_passing = models.BooleanField(default=False)
    notes = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="audits",
        db_index=True
    )
    auditor = models.ForeignKey(
        Auditor,
        on_delete=models.CASCADE,
        related_name="audits",
        db_index=True
    )

class Measurement(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True,blank=True)
    region = gis_models.PolygonField(srid=4326)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="measurements"
    )
