# GCP Resource Topology

## Architecture Diagram

```mermaid
graph TD
    subgraph "GCP Project (Sandbox — No Billing)"
        subgraph "BigQuery Datasets"
            BRONZE[fplip_bronze]
            SILVER[fplip_silver]
            GOLD[fplip_gold]
        end
        
        subgraph "Service Accounts"
            INGESTION[ingestion-sa]
            API[api-sa]
        end
        
        INGESTION -->|"BigQuery Data Editor"| BRONZE
        INGESTION -->|"BigQuery Data Editor"| SILVER
        INGESTION -->|"BigQuery Data Editor"| GOLD
        
        API -->|"BigQuery Data Viewer"| GOLD
        API -->|"BigQuery Job User (Project Level)"| GOLD
    end
    
    subgraph "External"
        AIRFLOW[Airflow DAGs]
        FASTAPI[FastAPI]
        DBT[dbt]
    end
    
    AIRFLOW -->|"Runs as"| INGESTION
    DBT -->|"Runs as"| INGESTION
    FASTAPI -->|"Runs as"| API



## IAM Roles Summary

| Service Account | Role | Resource | Purpose |
| :--- | :--- | :--- | :--- |
| **ingestion-sa** | BigQuery Data Editor | `fplip_bronze` | Write raw data |
| **ingestion-sa** | BigQuery Data Editor | `fplip_silver` | Transform data |
| **ingestion-sa** | BigQuery Data Editor | `fplip_gold` | Write aggregated data |
| **api-sa** | BigQuery Data Viewer | `fplip_gold` | Read serving data |
| **api-sa** | BigQuery Job User | Project Level | Execute queries |