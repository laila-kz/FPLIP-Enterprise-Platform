output "bronze_dataset_id" {
  value = google_bigquery_dataset.bronze.dataset_id
}

output "silver_dataset_id" {
  value = google_bigquery_dataset.silver.dataset_id
}

output "gold_dataset_id" {
  value = google_bigquery_dataset.gold.dataset_id
}

output "ingestion_sa_email" {
  value = google_service_account.ingestion_sa.email
}

output "api_sa_email" {
  value = google_service_account.api_sa.email
}