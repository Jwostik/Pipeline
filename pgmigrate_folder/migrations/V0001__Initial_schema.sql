CREATE TYPE stage_type AS ENUM ('HTTP', 'Postgres');
CREATE TYPE status_stage AS ENUM ('waiting', 'started', 'done');
CREATE TYPE status_text AS ENUM ('waiting', 'in process', 'success', 'error');
CREATE TYPE http_stage_method AS ENUM ('POST', 'GET');
create table pipelines (
    pipeline_id bigserial primary key,
    pipeline_name text unique);
create table stages (
    stage_id bigserial primary key,
    pipeline_id bigint references pipelines(pipeline_id),
    index_in_pipeline int,
    type stage_type,
    params jsonb,
    unique (pipeline_id, index_in_pipeline));
alter table pipelines add column first_stage bigint references stages(stage_id);
create table jobs_status (
    job_status_id bigserial primary key,
    pipeline_id bigint references pipelines(pipeline_id),
    stage_id bigint references stages(stage_id),
    job_status status_text,
    job_error text,
    data jsonb);
create table queue (
    stage_queue_id bigserial primary key,
    job_status_id bigint references jobs_status(job_status_id),
    status status_stage default 'waiting',
    started_time timestamp default CURRENT_TIMESTAMP);