# Hosting and APK Plan

## Free Hosting Recommendation

Use Render free web service for the Django container and Supabase free project for durable Postgres plus private prescription file storage.

Supabase project prepared:

- Project name: `Test`
- Project ref: `bleztdeqdgijhmyymdsn`
- Project URL: `https://bleztdeqdgijhmyymdsn.supabase.co`
- Database host: `db.bleztdeqdgijhmyymdsn.supabase.co`
- IPv4 pooler host: `aws-0-ap-southeast-2.pooler.supabase.com`
- Region: `ap-southeast-2`
- Private storage bucket: `prescriptions`

Reason:

- The app needs Python, OCR packages, Tesseract, uploads, and a database.
- Static hosts cannot run the Django/OCR backend.
- Render free can run the Dockerized Django app, but its local filesystem is ephemeral.
- Supabase can keep the database and prescription files durable outside the free web container.
- The hosted deployment uses Supabase Postgres, so `mysqlclient` is intentionally not included in `requirements.txt`.

## Required Hosted Environment Values

Set these on the hosting provider:

```text
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<generated secret>
DJANGO_ALLOWED_HOSTS=<your-host-domain>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-host-domain>
DATABASE_URL=postgresql://postgres.bleztdeqdgijhmyymdsn:<database-password>@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require
USE_S3_STORAGE=1
AWS_STORAGE_BUCKET_NAME=prescriptions
AWS_S3_ENDPOINT_URL=https://bleztdeqdgijhmyymdsn.storage.supabase.co/storage/v1/s3
AWS_S3_REGION_NAME=ap-southeast-2
AWS_S3_ACCESS_KEY_ID=<server-side-s3-access-key>
AWS_S3_SECRET_ACCESS_KEY=<server-side-s3-secret>
```

Values still needed from the Supabase dashboard:

- Database password for the `postgres` connection string.
- S3 access key ID and secret for Supabase Storage.

Do not put these secrets in Git.

If the database password contains special characters, URL-encode them in `DATABASE_URL`. For example, `@` must be written as `%40`.

## Supabase Schema Status

The Supabase project has these app tables:

- `public.records_patient`
- `public.records_document`
- `public.records_medicine`
- `public.django_migrations`
- `public.django_content_type`

Row level security is enabled on the app tables with no public browser policies. This is intentional for now because the Django backend should be the only service reading/writing prescription data.

## APK Recommendation

Build the APK as a web wrapper around the hosted HTTPS app. Do not wrap `localhost`; the mobile app needs a real hosted URL.

Good free path:

1. Deploy the Django app to a public HTTPS URL.
2. Generate an Android Trusted Web Activity or Capacitor wrapper that opens that URL.
3. Build a debug APK locally or with a free cloud builder.

Current blocker on this machine:

- Java exists.
- Node/npm exist.
- Android SDK/Gradle tooling is not installed.

Once Android SDK tooling is installed, the APK can be generated from the hosted URL and placed on the Desktop.
