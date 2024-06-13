CREATE VIEW vw_YearlyPaymentMetrics AS
SELECT
    LEFT(month_year, 4) AS year,
    payment_id,
    payment_type,
    SUM(total_times_used) AS total_times_used,
    SUM(total_revenue) AS total_revenue
FROM
    MonthlyPaymentMetrics
GROUP BY
    payment_id,
    payment_type,
    LEFT(month_year, 4);
GO
