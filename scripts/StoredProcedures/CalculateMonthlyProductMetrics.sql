CREATE PROCEDURE sp_CalculateMonthlyProductMetrics
AS
BEGIN

    -- Calculate metrics
    WITH ProductSales AS (
        SELECT
            FORMAT(t.[timestamp], 'yyyy-MM') AS month_year,
            p.product_category,
            p.product_id,
            COUNT(t.product_id) AS products_sold,
            SUM(t.total_amount) AS total_money_made
        FROM
            Transactions t
        JOIN
            Products p ON t.product_id = p.product_id
        GROUP BY
            p.product_id,
            P.product_category,
            FORMAT(t.[timestamp], 'yyyy-MM')
    )
    INSERT INTO MonthlyProductMetrics (month_year, product_category, product_id, products_sold, total_money_made)
    SELECT
        month_year,
        product_category,
        product_id,
        products_sold,
        total_money_made
    FROM
        ProductSales;
END;
GO
