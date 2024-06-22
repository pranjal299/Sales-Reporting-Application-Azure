CREATE PROCEDURE sp_CalculateMonthlyPaymentMetrics
AS
BEGIN

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
