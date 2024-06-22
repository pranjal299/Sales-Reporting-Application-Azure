CREATE PROCEDURE sp_CalculateMonthlyEmployeeMetrics
AS
BEGIN

    -- Calculate metrics
    WITH EmployeeSales AS (
        SELECT
            FORMAT(t.[timestamp], 'yyyy-MM') AS month_year,
            e.employee_state,
            e.employee_id,
            COUNT(DISTINCT(t.customer_id)) as unique_customers_serviced,
            COUNT(t.product_id) AS total_products_bought,
            SUM(t.total_amount) AS total_money_spent
        FROM
            Transactions t
        JOIN
            Employees e ON t.employee_id = e.employee_id
        GROUP BY
            e.employee_id,
            e.employee_state,
            FORMAT(t.[timestamp], 'yyyy-MM')
    )
    
    INSERT INTO MonthlyEmployeeMetrics (month_year, employee_state, employee_id, unique_customers_serviced, total_products_sold, total_money_made)
    SELECT
        month_year,
        employee_state,
        employee_id,
        unique_customers_serviced,
        total_products_bought,
        total_money_spent
    FROM
        EmployeeSales;

END;
GO
