CREATE VIEW vw_YearlyProductMetrics AS
SELECT
    LEFT(month_year, 4) AS year,
    product_category,
    product_id,
    SUM(products_sold) AS products_sold,
    SUM(total_money_made) AS total_money_made
FROM
    MonthlyProductMetrics
GROUP BY
    product_id,
    product_category,
    LEFT(month_year, 4);
GO
