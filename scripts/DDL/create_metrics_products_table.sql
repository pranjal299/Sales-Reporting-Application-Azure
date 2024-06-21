CREATE TABLE MonthlyProductMetrics (
            month_year NVARCHAR(7),
            product_category NVARCHAR(50),
            product_id INT,
            products_sold INT,
            total_money_made DECIMAL(18, 2)
            -- Optionally add avg_money_made_per_product
        );