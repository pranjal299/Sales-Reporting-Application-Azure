CREATE VIEW vw_QuarterlyCustomerMetrics AS
SELECT
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0)) AS quarter_year,
    customer_state,
    customer_id,
    SUM(total_products_bought) AS total_products_bought,
    SUM(total_money_spent) AS total_money_spent
FROM
    MonthlyCustomerMetrics
GROUP BY
    customer_id,
    customer_state,
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0));
GO
