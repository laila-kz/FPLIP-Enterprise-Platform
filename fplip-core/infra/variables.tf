variable "project_id" {
  description = "GCP project ID (Sandbox mode - no billing account linked)"
  type        = string
}

variable "region" {
  description = "Default GCP region for resources that need one"
  type        = string
  default     = "us-central1"
}

variable "dataset_location" {
  description = "BigQuery dataset location - must match across all three datasets"
  type        = string
  default     = "us"
}