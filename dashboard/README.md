---

# Dashboard

This directory contains a Streamlit-based dashboard application used to visualise and analyse processed food truck transaction data. It provides an interactive interface for exploring key business metrics and operational insights derived from the data pipeline.

---

## Overview

The dashboard is designed as a modular application, separating data access, transformation logic, and presentation layers. This structure improves maintainability and allows individual components to be extended or modified independently.

---

## Architecture

The dashboard consists of two main parts:

* A **Streamlit application (`app.py`)** that serves as the entry point and user interface
* A **core module package (`dashboard_core/`)** that encapsulates business logic, queries, and visual components

---

## Component Breakdown

### Application Layer

* **`app.py`**
  The main entry point for the Streamlit application. It defines the layout, handles user interaction, and orchestrates the rendering of charts and metrics.

* **`dashboard_wireframe.png`**
  A visual reference illustrating the intended layout and design of the dashboard interface.

* **`Dockerfile`**
  Provides a containerised environment for deploying the dashboard consistently across different systems.

---

### Core Modules (`dashboard_core/`)

* **`charts.py`**
  Defines visual components and chart generation logic used throughout the dashboard.

* **`clients.py`**
  Manages connections to external data sources (e.g. AWS Athena or APIs) and handles data retrieval.

* **`config.py`**
  Stores configuration settings such as environment variables, query parameters, and application constants.

* **`metrics.py`**
  Implements business logic for calculating key performance indicators (KPIs), such as revenue and transaction counts.

* **`queries.py`**
  Contains query definitions used to retrieve data from the underlying data storage layer.

* **`style.py`**
  Controls styling elements to ensure a consistent and readable user interface.

* **`transforms.py`**
  Applies data transformations required to prepare raw query results for visualisation.

* **`__init__.py`**
  Initialises the module package.

---

## Running the Dashboard

To launch the dashboard locally:

```bash
streamlit run app.py
```

This will start a local server and open the dashboard in a web browser.

---
