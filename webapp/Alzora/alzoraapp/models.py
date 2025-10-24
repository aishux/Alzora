from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPES = (
        ("patient", "Patient"),
        ("caretaker", "Caretaker"),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default="patient")

    def __str__(self):
        return f"{self.username} ({self.user_type})"



class Patients(models.Model):
    patient_id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=100, blank=True, null=True)
    safe_center_lat = models.FloatField(blank=True, null=True)
    safe_center_long = models.FloatField(blank=True, null=True)
    safe_radius_meters = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'patients'


class Caretakers(models.Model):
    caretaker_id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.CharField(unique=True, max_length=255)
    patient_ids = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'caretakers'


class Memories(models.Model):
    memory_id = models.BigAutoField(primary_key=True)
    patient_id = models.BigIntegerField()
    image_embedding = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    text_content = models.TextField(blank=True, null=True)
    text_embedding = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'memories'


class UsualSpots(models.Model):
    spot_id = models.BigAutoField(primary_key=True)
    patient_id = models.BigIntegerField()
    item_name = models.CharField(max_length=255)
    location_description = models.CharField(max_length=512, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'usual_spots'


class PatientMetadata(models.Model):
    metadata_id = models.BigAutoField(primary_key=True)
    patient_id = models.BigIntegerField()
    metadata_content = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'patient_metadata'
