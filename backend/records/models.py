from django.db import models


class Patient(models.Model):
    name = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    patient = models.ForeignKey(Patient, related_name="documents", on_delete=models.CASCADE)
    file = models.FileField(upload_to="prescriptions/%Y/%m/")
    original_name = models.CharField(max_length=260)
    file_type = models.CharField(max_length=120, blank=True)
    visit_date = models.DateField()
    doctor_name = models.CharField(max_length=160, blank=True)
    symptoms = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    extraction_status = models.CharField(max_length=260, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visit_date", "-created_at"]

    def __str__(self):
        return self.original_name


class Medicine(models.Model):
    document = models.ForeignKey(Document, related_name="medicines", on_delete=models.CASCADE)
    name = models.CharField(max_length=260)
    raw_line = models.TextField()
    dosage = models.CharField(max_length=120, blank=True)
    quantity = models.CharField(max_length=120, blank=True)
    frequency = models.CharField(max_length=120, blank=True)
    duration = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name
