CREATE PROCEDURE sp_CalculateMonthlyProductMetrics
AS
BEGIN
    -- Create a table to store monthly metrics
    IF OBJECT_ID('MonthlyProductMetrics', 'U') IS NOT NULL
        TRUNCATE TABLE MonthlyProductMetrics;
    ELSE
        CREATE TABLE MonthlyProductMetrics (
            month_year NVARCHAR(7),
            product_category NVARCHAR(50),
            product_id INT,
            products_sold INT,
            total_money_made DECIMAL(18, 2)
            -- Optionally add avg_money_made_per_product
        );

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
