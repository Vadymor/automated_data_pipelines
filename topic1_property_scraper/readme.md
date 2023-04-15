# Class Task. Property scraper
 
### 1) Present diagram of DAG and explain responsibility of each task in the DAG.

![alt text](https://github.com/Vadymor/automated_data_pipelines/blob/main/topic1_property_scraper/dag_schema.png?raw=true)

- *check_resource_availability* - make a request to web resource to check if it's available;
- *extract_Austin_communities_URL* - request to resource to get Austin communities;
- *download_Austin_communities_pages* - download communities HTML pages;
- *transform_Austin_communities_data* - transform HTML pages, extract needed data and store it;
- *extract_Austin_listings_URL* - for every community request to get listings;
- *download_Austin_listings_pages* - download listings HTML pages;
- *transform_Austin_listings_data* - transform HTML pages, extract needed data and store it.

### 2) Describe the approach that you plan to use for data extraction (API calIs, HTML parsing, etc.).

HTML parsing (resource doesn't have an API).

### 3) Propose some mechanism for data caching that will allow you to rerun data transformation without data extraction, when data transformation fails.

Store extracted data on persistent storage. If the transformation is failed, we will rerun it on previously stored data.
Moreover, we can apply the mechanic of flags to mark data that was processed, as a result, further transformations will know about the processing data status.

### 4) Describe all third-party tools (like AWS S3, AWS RDS) that you plan to use in your pipeline.

- AWS S3 - storing raw HTML pages;
- AWS RDS (Postgres) - storing URL and metadata about processed HTML pages, etc;
- AWS Redshift - central DWH for storing transformed data;
- AWS EC2, AWS Glue or AWS EMR - data transformations (it depends on data volume).

### 5) Analyze weak points in your pipeline (for tasks that would have potentially large execution time) and propose improvements that can be done in future.

Web resources could have limits on the number of requests and we should implement the mechanism of tracking these limits and prevent exceeding it.
Requesting and downloading HTML pages could take some time, we should consider it.
To speed up the entire process we could use async or thread to parallelize processes.