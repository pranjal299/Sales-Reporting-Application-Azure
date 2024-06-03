# Financial Transaction Data Pipeline Project

This project involves building a data pipeline to process and visualize financial transactional data using Azure services. The pipeline includes data ingestion, validation, preprocessing, KPI calculation, and visualization using Power BI.

## Project Overview

1. **Data Ingestion**: Collect data files and store them in Azure Data Lake Storage.
2. **Data Validation and Preprocessing**: Validate and preprocess the data before ingestion into Azure SQL Database using custom Python scripts.
3. **Data Storage**: Store the validated and cleaned data in Azure SQL Database.
4. **KPI Calculation**: Create KPI tables based on the transactional data for various time periods.
5. **Data Visualization**: Visualize the KPIs using Power BI.

## Tools and Technologies

- **Azure Data Lake Storage**: For storing raw and processed data files.
- **Azure Data Factory**: For orchestrating data ingestion and processing pipelines.
- **Azure SQL Database**: For storing cleaned and validated data.
- **Python**: For custom scripts to validate and preprocess data.
- **Power BI**: For visualizing the KPIs.
- **Azure Synapse Analytics** (optional): For advanced analytics and big data processing.

## Project Steps

1. **Data Ingestion**:
   - Store CSV files (transactions, employees, payments, products, customers) in Azure Data Lake Storage.

2. **Data Validation and Preprocessing**:
   - Use Python scripts to perform basic validation checks (e.g., missing values, duplicates).
   - Preprocess the data (e.g., data type conversions, handling missing values).

3. **Data Storage**:
   - Upload the cleaned data to Azure SQL Database using custom scripts or Azure Data Factory.

4. **KPI Calculation**:
   - Create stored procedures in Azure SQL Database to calculate KPIs such as the number of accounts opened, the number of transactions, and the total transaction amount for various time periods.

5. **Data Visualization**:
   - Connect Power BI to Azure SQL Database.
   - Import KPI tables and create dashboards to visualize the data.

## How to Run the Project

1. **Set Up Azure Services**:
   - Set up Azure Data Lake Storage, Azure SQL Database, and Azure Data Factory.

2. **Ingest Data**:
   - Upload the provided CSV files to Azure Data Lake Storage.

3. **Validate and Preprocess Data**:
   - Run the provided Python scripts to validate and preprocess the data.

4. **Store Data in Azure SQL Database**:
   - Use custom scripts or Azure Data Factory to upload the cleaned data to Azure SQL Database.

5. **Calculate KPIs**:
   - Execute the stored procedures in Azure SQL Database to calculate the KPIs.

6. **Visualize Data in Power BI**:
   - Connect Power BI to Azure SQL Database and create dashboards to visualize the KPIs.


