CREATE TABLE MonthlyCustomerMetrics (
            month_year NVARCHAR(7),
            customer_state NVARCHAR(20),
            customer_id INT,
            total_products_bought INT,
            total_money_spent DECIMAL(18, 2)
            -- Optionally add avg_money_spent_per_order/product
        );