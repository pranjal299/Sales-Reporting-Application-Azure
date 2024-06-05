CREATE VIEW vw_QuarterlyPaymentMetrics AS
SELECT
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0)) AS quarter_year,
    payment_id,
    payment_type,
    SUM(total_times_used) AS total_times_used,
    SUM(total_revenue) AS total_revenue
FROM
    MonthlyPaymentMetrics
GROUP BY
    payment_id,
    payment_type,
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0));
GO
