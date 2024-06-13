CREATE PROCEDURE sp_CalculateMonthlyPaymentMetrics
AS
BEGIN
    -- Create a table to store monthly metrics
    IF OBJECT_ID('MonthlyPaymentMetrics', 'U') IS NOT NULL
        TRUNCATE TABLE MonthlyPaymentMetrics;
    ELSE
        CREATE TABLE MonthlyPaymentMetrics (
            month_year NVARCHAR(7),
            payment_id INT,
            payment_type NVARCHAR(20),
            unique_customer_usage INT,
            total_times_used INT,
            total_revenue DECIMAL(18, 2)
            -- Optionally add avg_money_spent_per_order/product
        );

    -- Calculate metrics
    WITH PaymentSales AS (
        SELECT
            FORMAT(t.[timestamp], 'yyyy-MM') AS month_year,
            p.payment_id,
            p.payment_type,
            COUNT(DISTINCT(t.customer_id)) as unique_customer_usage,
            COUNT(t.payment_id) AS total_times_used,
            SUM(t.total_amount) AS total_revenue
        FROM
            Transactions t
        JOIN
            Payments p ON t.payment_id = p.payment_id
        GROUP BY
            p.payment_id,
            p.payment_type,
            FORMAT(t.[timestamp], 'yyyy-MM')
    )
    
    INSERT INTO MonthlyPaymentMetrics (month_year, payment_id, payment_type, unique_customer_usage, total_times_used, total_revenue)
    SELECT
        month_year,
        payment_id,
        payment_type,
        unique_customer_usage,
        total_times_used,
        total_revenue
    FROM
        PaymentSales;

END;
GO
