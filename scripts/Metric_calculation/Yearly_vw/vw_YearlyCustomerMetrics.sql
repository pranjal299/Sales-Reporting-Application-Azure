CREATE VIEW vw_YearlyCustomerMetrics AS
SELECT
    LEFT(month_year, 4) AS year,
    customer_state,
    customer_id,
    SUM(total_products_bought) AS total_products_bought,
    SUM(total_money_spent) AS total_money_spent
FROM
    MonthlyCustomerMetrics
GROUP BY
    customer_id,
    customer_state,
    LEFT(month_year, 4);
GO