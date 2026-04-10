---

# Pipeline

This directory contains the ETL pipeline responsible for processing food truck transaction data sourced from an RDS database and storing it in Amazon S3 using a partitioned data layout optimised for querying.

---

## Overview

The pipeline implements a four-stage ETL process to ensure data is extracted, cleaned, structured, and stored efficiently for downstream analytics.

---

## Pipeline Workflow

### 1. Extraction (`extract.py`)

* Establishes a connection to the RDS database using credentials provided via environment variables
* Retrieves transaction data from a recent time window (e.g. the last three hours)
* Extracts supporting dimension data, including food truck details and payment methods

---

### 2. Transformation (`transform.py`)

* Joins transaction data with relevant dimension tables
* Performs data cleaning operations, such as:

  * standardising payment method values
  * removing unnecessary whitespace
* Filters out incomplete or invalid records to ensure data quality
* Derives partitioning columns (year, month, day) from transaction timestamps

---

### 3. Upload to S3 (`load.py`)

* Converts the processed dataset into Parquet format for efficient storage and querying
* Structures the output into a hierarchical directory layout based on truck name and date
* Uploads the partitioned Parquet files to an S3 bucket
* Maintains a consistent directory structure:

```plaintext id="l5i9rk"
transaction/{truck_name}/year={year}/month={month}/day={day}/
```

---

## Execution

The pipeline is orchestrated through a central script:

```bash id="k6j5ec"
python main.py
```

This entry point coordinates all stages of the ETL process in sequence.

---

## Infrastructure and Supporting Components

* **Terraform (`terraform/`)**
  Manages the provisioning of AWS resources, including S3 buckets, AWS Glue crawlers, and associated data catalog components


* **Dockerfile**
  Defines a containerised environment for consistent deployment and execution of the pipeline

---
