CREATE VIEW vw_QuarterlyEmployeeMetrics AS
SELECT
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0)) AS quarter_year,
    employee_state,
    employee_id,
    SUM(unique_customers_serviced) AS unique_customers_serviced,
    SUM(total_products_sold) AS total_products_sold,
    SUM(total_money_made) AS total_money_made

FROM
    MonthlyEmployeeMetrics
GROUP BY
    employee_id,
    employee_state,
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0));
GO
