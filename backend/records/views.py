import json

from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .extraction import extract_prescription_date, extract_text, parse_medicines
from .models import Document, Medicine, Patient


@csrf_exempt
@require_http_methods(["GET", "POST"])
def patients(request):
    if request.method == "POST":
        payload = json.loads(request.body or "{}")
        patient = Patient.objects.create(name=payload["name"].strip())
        return JsonResponse(serialize_patient(patient), status=201)

    return JsonResponse({"patients": [serialize_patient(patient) for patient in Patient.objects.all()]})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def documents(request):
    if request.method == "POST":
        patient = get_object_or_404(Patient, id=request.POST["patient_id"])
        upload = request.FILES["file"]
        manual_text = request.POST.get("document_text", "").strip()
        extracted_text, extraction_status = extract_text(upload, upload.content_type or "")
        combined_text = "\n".join(part for part in [extracted_text, manual_text] if part)
        prescribed_date = extract_prescription_date(combined_text) or request.POST["visit_date"]

        document = Document.objects.create(
            patient=patient,
            file=upload,
            original_name=upload.name,
            file_type=upload.content_type or "",
            visit_date=prescribed_date,
            doctor_name=request.POST.get("doctor_name", "").strip(),
            symptoms=request.POST.get("symptoms", "").strip(),
            extracted_text=combined_text,
            extraction_status=extraction_status if extracted_text else "No text extracted; manual text may be needed",
        )

        Medicine.objects.bulk_create(
            Medicine(document=document, **medicine)
            for medicine in parse_medicines(combined_text)
        )
        document.refresh_from_db()
        return JsonResponse(serialize_document(document), status=201)

    patient_id = request.GET.get("patient_id")
    queryset = Document.objects.select_related("patient").prefetch_related("medicines")
    if patient_id:
        queryset = queryset.filter(patient_id=patient_id)
    return JsonResponse({"documents": [serialize_document(document) for document in queryset]})


@csrf_exempt
@require_http_methods(["DELETE"])
def document_detail(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    document.file.delete(save=False)
    document.delete()
    return JsonResponse({"deleted": True})


@require_http_methods(["GET"])
def document_file(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    return FileResponse(document.file.open("rb"), content_type=document.file_type or "application/octet-stream")


@require_http_methods(["GET"])
def search(request):
    query = request.GET.get("q", "").strip()
    patient_id = request.GET.get("patient_id")
    documents = Document.objects.select_related("patient").prefetch_related("medicines")

    if patient_id:
        documents = documents.filter(patient_id=patient_id)

    if query:
        documents = documents.filter(
            Q(patient__name__icontains=query)
            | Q(original_name__icontains=query)
            | Q(doctor_name__icontains=query)
            | Q(symptoms__icontains=query)
            | Q(extracted_text__icontains=query)
            | Q(medicines__name__icontains=query)
            | Q(medicines__raw_line__icontains=query)
        ).distinct()

    rows = []
    for document in documents:
        medicines = list(document.medicines.all())
        if not medicines:
            if not query or document_matches_query(document, query):
                rows.append(serialize_search_row(document, None))
            continue

        matching_medicines = [medicine for medicine in medicines if medicine_matches_query(medicine, query)]
        if query and matching_medicines:
            rows.extend(serialize_search_row(document, medicine) for medicine in matching_medicines)
            continue

        if query and document_matches_query(document, query):
            rows.extend(serialize_search_row(document, medicine) for medicine in medicines)
            continue

        for medicine in medicines:
            rows.append(serialize_search_row(document, medicine))

    return JsonResponse({"rows": rows})


def document_matches_query(document, query):
    return query.lower() in " ".join([
        document.patient.name,
        document.original_name,
        document.doctor_name,
        document.symptoms,
        str(document.visit_date),
    ]).lower()


def medicine_matches_query(medicine, query):
    if not query:
        return True

    return query.lower() in medicine_search_blob(medicine)


def medicine_search_blob(medicine):
    return " ".join([
        medicine.name,
        medicine.raw_line,
        medicine.dosage,
        medicine.quantity,
        medicine.frequency,
        medicine.duration,
    ]).lower()


def serialize_patient(patient):
    return {
        "id": patient.id,
        "name": patient.name,
        "document_count": getattr(patient, "document_count", None) or patient.documents.count(),
    }


def serialize_document(document):
    visit_date = document.visit_date.isoformat() if hasattr(document.visit_date, "isoformat") else document.visit_date
    return {
        "id": document.id,
        "patient_id": document.patient_id,
        "patient_name": document.patient.name,
        "file_name": document.original_name,
        "file_type": document.file_type,
        "file_url": f"/api/documents/{document.id}/file/",
        "visit_date": visit_date,
        "doctor_name": document.doctor_name,
        "symptoms": document.symptoms,
        "extracted_text": document.extracted_text,
        "extraction_status": document.extraction_status,
        "medicines": [serialize_medicine(medicine) for medicine in document.medicines.all()],
    }


def serialize_medicine(medicine):
    return {
        "id": medicine.id,
        "name": medicine.name,
        "raw_line": medicine.raw_line,
        "dosage": medicine.dosage,
        "quantity": medicine.quantity,
        "frequency": medicine.frequency,
        "duration": medicine.duration,
    }


def serialize_search_row(document, medicine):
    return {
        "document": serialize_document(document),
        "medicine": serialize_medicine(medicine) if medicine else None,
    }
