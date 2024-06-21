CREATE TABLE MonthlyPaymentMetrics (
            month_year NVARCHAR(7),
            payment_id INT,
            payment_type NVARCHAR(20),
            unique_customer_usage INT,
            total_times_used INT,
            total_revenue DECIMAL(18, 2)
            -- Optionally add avg_money_spent_per_order/product
        );