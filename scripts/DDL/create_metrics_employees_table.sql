CREATE TABLE MonthlyEmployeeMetrics (
            month_year NVARCHAR(7),
            employee_state NVARCHAR(20),
            employee_id INT,
            unique_customers_serviced INT,
            total_products_sold INT,
            total_money_made DECIMAL(18, 2)
            -- Optionally add avg_money_spent_per_order/product
        );