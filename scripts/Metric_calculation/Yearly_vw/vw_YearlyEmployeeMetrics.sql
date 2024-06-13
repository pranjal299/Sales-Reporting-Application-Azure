CREATE VIEW vw_YearlyEmployeeMetrics AS
SELECT
    LEFT(month_year, 4) AS year,
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
    LEFT(month_year, 4);
GO
