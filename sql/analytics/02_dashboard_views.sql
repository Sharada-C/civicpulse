CREATE OR REPLACE VIEW dashboard_overview AS

SELECT
    COUNT(*) AS total_complaints,

    COUNT(*) FILTER (
        WHERE status = 'OPEN'
    ) AS open_complaints,

    COUNT(*) FILTER (
        WHERE status = 'IN_PROGRESS'
    ) AS in_progress_complaints,

    COUNT(*) FILTER (
        WHERE status IN ('RESOLVED', 'CLOSED')
    ) AS resolved_complaints,

    ROUND(
        100.0
        * COUNT(*) FILTER (
            WHERE status IN ('RESOLVED', 'CLOSED')
        )
        / NULLIF(COUNT(*), 0),
        2
    ) AS resolution_rate_percent,

    ROUND(
        AVG(resolution_time_days),
        2
    ) AS avg_actual_resolution_days,

    ROUND(
        AVG(predicted_resolution_days),
        2
    ) AS avg_predicted_resolution_days,

    COUNT(*) FILTER (
        WHERE severity_score = 1.00
    ) AS critical_actual_complaints,

    COUNT(*) FILTER (
        WHERE predicted_severity = 'CRITICAL'
    ) AS critical_predicted_complaints,

    COUNT(*) FILTER (
        WHERE predicted_severity IN ('HIGH', 'CRITICAL')
    ) AS high_risk_predicted_complaints,

    ROUND(
        100.0
        * AVG(
            CASE
                WHEN is_repeat_complaint THEN 1.0
                ELSE 0.0
            END
        ),
        2
    ) AS repeat_complaint_rate_percent

FROM fact_complaints;