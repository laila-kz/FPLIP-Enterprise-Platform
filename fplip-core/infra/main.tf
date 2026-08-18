resource "google_bigquery_dataset" "bronze" {
  dataset_id                  = "fplip_bronze"
  friendly_name               = "FPLIP Bronze Dataset"
  description                 = "Raw ingested data from factory sources"
  location                    = var.dataset_location
  default_table_expiration_ms = 5184000000  # 60 days (Sandbox max)
  default_partition_expiration_ms = 5184000000  # 60 days (Sandbox max)
  project                     = var.project_id
}

resource "google_bigquery_dataset" "silver" {
  dataset_id                  = "fplip_silver"
  friendly_name               = "FPLIP Silver Dataset"
  description                 = "Cleaned and transformed data"
  location                    = var.dataset_location
  default_table_expiration_ms = 5184000000  # 60 days (Sandbox max)
  default_partition_expiration_ms = 5184000000  # 60 days (Sandbox max)
  project                     = var.project_id
}

resource "google_bigquery_dataset" "gold" {
  dataset_id                  = "fplip_gold"
  friendly_name               = "FPLIP Gold Dataset"
  description                 = "Aggregated and business-ready data"
  location                    = var.dataset_location
  default_table_expiration_ms = 5184000000  # 60 days (Sandbox max)
  default_partition_expiration_ms = 5184000000  # 60 days (Sandbox max)
  project                     = var.project_id
}


resource "google_service_account" "ingestion_sa" {
  account_id   = "ingestion-sa"
  display_name = "FPLIP Ingestion Service Account"
  description  = "Used by Airflow/dbt to load and transform Bronze/Silver/Gold"
  project      = var.project_id
}

resource "google_service_account" "api_sa" {
  account_id   = "api-sa"
  display_name = "FPLIP API Service Account"
  description  = "Used by the read-only FastAPI service against fplip_gold"
  project      = var.project_id
}

# Ingestion SA - Write access to all three datasets
resource "google_bigquery_dataset_iam_member" "ingestion_bronze_editor" {
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

resource "google_bigquery_dataset_iam_member" "ingestion_silver_editor" {
  dataset_id = google_bigquery_dataset.silver.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

resource "google_bigquery_dataset_iam_member" "ingestion_gold_editor" {
  dataset_id = google_bigquery_dataset.gold.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingestion_sa.email}"
}

# API SA - Read-only access to Gold only
resource "google_bigquery_dataset_iam_member" "api_gold_viewer" {
  dataset_id = google_bigquery_dataset.gold.dataset_id
  project    = var.project_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.api_sa.email}"
}

# API SA - Required project-level jobUser permission (explained above)
resource "google_project_iam_member" "api_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}