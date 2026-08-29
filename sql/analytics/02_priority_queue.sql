CREATE OR REPLACE VIEW priority_queue AS

SELECT
    ward_code,
    ward_name,
    category_name,
    complaint_count,
    complaints_per_10000,
    severity_score,
    repeat_rate_percent,
    avg_resolution_days,
    priority_score,

    CASE
        WHEN priority_score >= 0.65 THEN 'CRITICAL'
        WHEN priority_score >= 0.60 THEN 'HIGH'
        WHEN priority_score >= 0.55 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS priority_level

FROM ward_category_priority;