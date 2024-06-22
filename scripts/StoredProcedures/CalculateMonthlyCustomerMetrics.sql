CREATE PROCEDURE sp_CalculateMonthlyCustomerMetrics
AS
BEGIN
    -- Calculate metrics
    WITH CustomerSales AS (
        SELECT
            FORMAT(t.[timestamp], 'yyyy-MM') AS month_year,
            c.customer_state,
            c.customer_id,
            COUNT(t.product_id) AS total_products_bought,
            SUM(t.total_amount) AS total_money_spent
        FROM
            Transactions t
        JOIN
            Customers c ON t.customer_id = c.customer_id
        GROUP BY
            c.customer_id,
            c.customer_state,
            FORMAT(t.[timestamp], 'yyyy-MM')
    )
    
    INSERT INTO MonthlyCustomerMetrics (month_year, customer_state, customer_id, total_products_bought, total_money_spent)
    SELECT
        month_year,
        customer_state,
        customer_id,
        total_products_bought,
        total_money_spent
    FROM
        CustomerSales;

END;
GO
