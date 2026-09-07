# Medicine Finder

Medicine Finder is a local-first web/mobile PWA prototype for storing prescription PDFs or photos by patient and searching previous medicines, symptoms, doctors, and visit dates.

## Current MVP

- Add multiple patients.
- Upload PDF or image prescription documents.
- Save visit date, doctor, symptoms or diagnosis, and prescription text.
- Extract text from machine-readable PDFs.
- OCR scanned PDFs by rendering pages locally with PyMuPDF and reading them with Tesseract.
- OCR uploaded prescription images with Tesseract.
- Detect likely medicine lines from extracted PDF/image text.
- Parse medicine name, dosage, quantity, frequency, and duration when the prescription text contains them.
- Search by medicine, symptom, diagnosis, doctor, date, patient, document name, extracted prescription text, dosage, quantity, frequency, or duration.
- Preview the original uploaded PDF/image from the result table.
- Store patients, documents, and medicines in Django models using SQLite by default.

## Run

No Flutter or Dart is required. This version is a Django-backed browser app that also works on mobile as a PWA.

```powershell
python -m pip install --user -r requirements.txt
python backend/manage.py migrate
npm start
```

Then open `http://localhost:5173`.

If Node/npm is not available, run this directly:

```powershell
python backend/manage.py runserver 5173
```

## Free Hosting and APK

For a hosted version, use a free Python container host for Django and keep durable data/files outside the container.

Recommended free MVP setup:

- Render free web service for the Dockerized Django app.
- Supabase project `Test` for hosted Postgres at `db.bleztdeqdgijhmyymdsn.supabase.co`.
- Supabase IPv4 pooler at `aws-0-ap-southeast-2.pooler.supabase.com` for Render.
- Supabase Storage bucket `prescriptions` for private prescription PDFs/images.
- Android APK as a wrapper around the final hosted HTTPS URL.

Why not SQLite for hosting:

SQLite is good for local development, but free web hosts usually use ephemeral filesystems. Uploaded documents and `db.sqlite3` can be lost after redeploys, restarts, or idle spin-downs. For hosting, use Supabase/Postgres plus storage.

Deployment files added:

- `Dockerfile` installs Python dependencies plus Tesseract OCR.
- `render.yaml` defines a Render free web service.
- `.env.example` lists the required hosted environment variables.
- `docs/hosting-and-apk.md` has the hosting and APK plan.

Supabase setup completed:

- App tables were created in project `bleztdeqdgijhmyymdsn`.
- Django migration markers were added for the current schema.
- Private storage bucket `prescriptions` was created.
- A risky public `SECURITY DEFINER` function execute permission was revoked after Supabase advisors flagged it.

Still needed from Supabase dashboard or your password manager:

- Database password for `DATABASE_URL`.
- S3 access key ID and secret for private file storage.

Use the pooler format for free hosting:

```text
postgresql://postgres.bleztdeqdgijhmyymdsn:<database-password>@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require
```

APK requirement:

The APK should wrap the hosted HTTPS app, not `localhost`. To build it locally, this machine also needs Android SDK/Gradle tooling. Java and Node are installed, but Android SDK is not currently installed.

## Database Choice

SQLite is still the right default for this stage because it is free, zero-config, easy to back up, and works well for a single-user local medical document archive. OCR/search quality does not require MySQL, Supabase, or any hosted database. MySQL or Supabase become useful later when you need multi-device access, user accounts, hosted deployment, backups, or sharing with family members.

Django is configured so you can switch to MySQL later with environment variables:

```powershell
$env:DATABASE_ENGINE="mysql"
$env:MYSQL_DATABASE="medicine_finder"
$env:MYSQL_USER="your_user"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
```

You would also need to install a compatible MySQL driver such as `mysqlclient` or `PyMySQL`.
Do not add `mysqlclient` to Render unless you switch the hosted app to MySQL; the current hosted path uses Supabase Postgres.

Supabase is a good later option if you want hosted Postgres, authentication, file storage, and sync across web/mobile devices. For that path, row-level security and private file access need to be designed before putting prescription data online.

## OCR Note

PDF text extraction works for machine-readable PDFs. Scanned PDFs and images require the Tesseract executable installed and available on `PATH`; this machine already has `tesseract.exe` visible to the app. If OCR misses text because of handwriting, low image quality, or unusual layout, use the optional additional text box as a correction/fallback.

## Privacy Note

Prescription files and medical details are sensitive health data. A production app should include authentication, encryption at rest, audit logs, backups, and explicit patient data deletion/export flows.
