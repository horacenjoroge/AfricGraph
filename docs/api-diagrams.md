# API Flow Diagrams

Visual representations of API request flows and data processing.

## Authentication Flow

```
Client                    API Gateway              Auth Service
  |                            |                        |
  |-- POST /auth/login ------->|                        |
  |                            |-- Validate Credentials->|
  |                            |<-- User Data -----------|
  |                            |-- Generate JWT ------->|
  |                            |<-- JWT Token ----------|
  |<-- 200 OK + Token ---------|                        |
  |                            |                        |
```

## Risk Assessment Flow

```
Client                    API                    Services
  |                        |                        |
  |-- GET /risk/{id} ----->|                        |
  |                        |-- Check Cache -------->Redis
  |                        |<-- Cache Miss ---------|
  |                        |                        |
  |                        |-- Query Payment ----->Neo4j
  |                        |-- Query Supplier ----->Neo4j
  |                        |-- Query Ownership ---->Neo4j
  |                        |-- Query Cashflow ----->PostgreSQL
  |                        |                        |
  |                        |-- Calculate Score ---->Risk Engine
  |                        |-- Store in Cache ----->Redis
  |                        |-- Persist History ---->PostgreSQL
  |<-- 200 OK + Score ------|                        |
```

## Fraud Detection Flow

```
Scheduler              Fraud Detector           Neo4j
  |                          |                    |
  |-- Trigger Scan --------->|                    |
  |                          |                    |
  |                          |-- Pattern 1 ------->|
  |                          |-- Pattern 2 ------->|
  |                          |-- Pattern 3 ------->|
  |                          |-- Pattern 4 ------->|
  |                          |-- Pattern 5 ------->|
  |                          |-- Pattern 6 ------->|
  |                          |-- Pattern 7 ------->|
  |                          |<-- Results ---------|
  |                          |                    |
  |                          |-- Aggregate ------->|
  |                          |-- Create Alert ---->PostgreSQL
  |                          |-- Notify ---------->Alert System
  |<-- Complete --------------|                    |
```

## Graph Query Flow

```
Client                    API                    Query Rewriter
  |                        |                            |
  |-- GET /graph/{id} ---->|                            |
  |                        |-- Extract Subject -------->|
  |                        |-- Build Filters --------->|
  |                        |                            |
  |                        |-- Rewrite Query --------->|
  |                        |                            |
  |                        |-- Execute Query --------->Neo4j
  |                        |<-- Results ---------------|
  |                        |                            |
  |                        |-- Cache Result ---------->Redis
  |<-- 200 OK + Graph ------|                            |
```

## Permission-Aware Query Flow

```
Request                  ABAC Middleware         Policy Engine
  |                            |                        |
  |-- Request with Token ----->|                        |
  |                            |-- Extract Subject ---->|
  |                            |-- Get Resource ------->|
  |                            |-- Get Environment ---->|
  |                            |                        |
  |                            |-- Evaluate Policies -->|
  |                            |<-- Decision -----------|
  |                            |                        |
  |                            |-- Check Cache -------->Redis
  |                            |<-- Cached Decision ----|
  |                            |                        |
  |                            |-- Allow/Deny --------->|
  |<-- Response ----------------|                        |
```

## Data Ingestion Flow

```
Client                    API                    Ingestion Pipeline
  |                        |                            |
  |-- POST /ingest ------->|                            |
  |                        |-- Validate Data --------->|
  |                        |-- Create Job ------------>PostgreSQL
  |                        |                            |
  |                        |-- Queue Task ----------->RabbitMQ
  |<-- 202 Accepted --------|                            |
  |                        |                            |
  |                        |-- Process Data ---------->Celery Worker
  |                        |-- Normalize ------------->|
  |                        |-- Create Nodes ---------->Neo4j
  |                        |-- Create Relationships -->Neo4j
  |                        |-- Index Data ------------>Elasticsearch
  |                        |-- Update Job Status ---->PostgreSQL
  |                        |                            |
```

## Search Flow

```
Client                    API                    Elasticsearch
  |                        |                            |
  |-- GET /search?q=... -->|                            |
  |                        |-- Parse Query ----------->|
  |                        |-- Check Cache ----------->Redis
  |                        |<-- Cache Miss ------------|
  |                        |                            |
  |                        |-- Search Index --------->|
  |                        |<-- Results ---------------|
  |                        |                            |
  |                        |-- Cache Results --------->Redis
  |                        |-- Format Response ------->|
  |<-- 200 OK + Results ----|                            |
```

## Workflow Approval Flow

```
User                    API                    Workflow Engine
  |                      |                          |
  |-- POST /approve ---->|                          |
  |                      |-- Get Instance ---------->PostgreSQL
  |                      |-- Validate Step -------->|
  |                      |-- Update Status -------->PostgreSQL
  |                      |-- Move to Next --------->|
  |                      |                          |
  |                      |-- Send Notification ---->Notification Service
  |                      |-- Log Action ----------->PostgreSQL
  |<-- 200 OK ------------|                          |
```

## Backup Flow

```
Scheduler            Backup Orchestrator        Services
  |                          |                      |
  |-- Trigger Backup ------->|                      |
  |                          |                      |
  |                          |-- Backup Neo4j ----->Neo4j
  |                          |-- Backup PostgreSQL->PostgreSQL
  |                          |-- Backup Redis ------>Redis
  |                          |                      |
  |                          |-- Test Backups ----->Backup Tester
  |                          |<-- Test Results -----|
  |                          |                      |
  |                          |-- Upload to Cloud --->S3/GCS/Azure
  |                          |-- Apply Retention --->Retention Policy
  |<-- Complete --------------|                      |
```
