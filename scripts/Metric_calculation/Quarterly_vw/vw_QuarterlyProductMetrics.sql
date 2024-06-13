CREATE VIEW vw_QuarterlyProductMetrics AS
SELECT
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0)) AS quarter_year,
    product_category,
    product_id,
    SUM(products_sold) AS products_sold,
    SUM(total_money_made) AS total_money_made
FROM
    MonthlyProductMetrics
GROUP BY
    product_id,
    product_category,
    CONCAT(LEFT(month_year, 4), '-Q', CEILING(CAST(RIGHT(month_year, 2) AS INT) / 3.0));
GO
