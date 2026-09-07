from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .extraction import extract_prescription_date, parse_medicines


class RecordsApiTests(TestCase):
    def test_upload_with_manual_text_creates_searchable_medicine(self):
        patient_response = self.client.post(
            "/api/patients/",
            data={"name": "Test Patient"},
            content_type="application/json",
        )
        self.assertEqual(patient_response.status_code, 201)
        patient_id = patient_response.json()["id"]

        upload = SimpleUploadedFile(
            "prescription.txt",
            b"placeholder",
            content_type="application/octet-stream",
        )
        document_response = self.client.post(
            "/api/documents/",
            data={
                "patient_id": patient_id,
                "file": upload,
                "visit_date": "2026-09-04",
                "doctor_name": "Dr Test",
                "symptoms": "fever cough",
                "document_text": "Tab Azithromycin 500mg - once daily for 3 days",
            },
        )
        self.assertEqual(document_response.status_code, 201)

        search_response = self.client.get("/api/search/", {"q": "azithromycin"})
        self.assertEqual(search_response.status_code, 200)
        rows = search_response.json()["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["medicine"]["name"], "Azithromycin")
        self.assertEqual(rows[0]["medicine"]["dosage"], "500mg")
        self.assertEqual(rows[0]["medicine"]["quantity"], "3 doses estimated")

    def test_parses_explicit_quantity_duration_and_frequency(self):
        medicines = parse_medicines("Tab Dolo 650mg qty 10 - TDS for 3 days")

        self.assertEqual(len(medicines), 1)
        self.assertEqual(medicines[0]["name"], "Dolo")
        self.assertEqual(medicines[0]["dosage"], "650mg")
        self.assertEqual(medicines[0]["quantity"], "qty 10")
        self.assertEqual(medicines[0]["frequency"], "TDS")
        self.assertEqual(medicines[0]["duration"], "for 3 days")

    def test_numbered_prescription_block_keeps_schedule_with_medicine(self):
        medicines = parse_medicines("""
Rx
Medicine/Dosage
Duration
1.
SEPTILIN SYP
5 - Syrup - Morning , 5 - Syrup - Night
7 Day(s)
2.
MUCOLITE SYRUP
2.5 - Syrup - Morning , 2.5 - Syrup - Night
With food
5 Day(s)
""")

        self.assertEqual(len(medicines), 2)
        mucolite = medicines[1]
        self.assertEqual(mucolite["name"], "MUCOLITE SYRUP")
        self.assertEqual(mucolite["quantity"], "2.5")
        self.assertEqual(mucolite["frequency"], "Morning, Night")
        self.assertEqual(mucolite["duration"], "5 Day(s)")

    def test_extracts_indian_prescription_date(self):
        self.assertEqual(
            extract_prescription_date("Date:\n 15/03/2025"),
            __import__("datetime").date(2025, 3, 15),
        )

    def test_medicine_search_returns_only_matching_medicine_rows(self):
        patient_response = self.client.post(
            "/api/patients/",
            data={"name": "Search Patient"},
            content_type="application/json",
        )
        patient_id = patient_response.json()["id"]
        upload = SimpleUploadedFile(
            "prescription.txt",
            b"placeholder",
            content_type="application/octet-stream",
        )
        self.client.post(
            "/api/documents/",
            data={
                "patient_id": patient_id,
                "file": upload,
                "visit_date": "2026-09-04",
                "document_text": """
Date:
15/03/2025
1.
BILDIM 100ML SYRUP
10 - Syrup - Morning
7 Day(s)
2.
MUCOLITE SYRUP
2.5 - Syrup - Morning , 2.5 - Syrup - Night
5 Day(s)
""",
            },
        )

        search_response = self.client.get("/api/search/", {"q": "Mucolite"})
        rows = search_response.json()["rows"]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["medicine"]["name"], "MUCOLITE SYRUP")
        self.assertEqual(rows[0]["document"]["visit_date"], "2025-03-15")

    def test_machine_readable_pdf_text_becomes_searchable(self):
        import fitz

        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Tab Cetirizine 10mg qty 5 - once daily for 5 days")
        pdf_bytes = pdf.tobytes()
        pdf.close()

        patient_response = self.client.post(
            "/api/patients/",
            data={"name": "PDF Patient"},
            content_type="application/json",
        )
        patient_id = patient_response.json()["id"]
        upload = SimpleUploadedFile(
            "prescription.pdf",
            pdf_bytes,
            content_type="application/pdf",
        )

        document_response = self.client.post(
            "/api/documents/",
            data={
                "patient_id": patient_id,
                "file": upload,
                "visit_date": "2026-09-04",
                "symptoms": "allergy",
            },
        )
        self.assertEqual(document_response.status_code, 201)

        search_response = self.client.get("/api/search/", {"q": "cetirizine"})
        rows = search_response.json()["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["medicine"]["name"], "Cetirizine")
        self.assertEqual(rows[0]["medicine"]["quantity"], "qty 5")
