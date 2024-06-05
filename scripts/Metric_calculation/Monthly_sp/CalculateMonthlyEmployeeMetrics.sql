CREATE PROCEDURE sp_CalculateMonthlyEmployeeMetrics
AS
BEGIN
    -- Create a table to store monthly metrics
    IF OBJECT_ID('MonthlyEmployeeMetrics', 'U') IS NOT NULL
        TRUNCATE TABLE MonthlyEmployeeMetrics;
    ELSE
        CREATE TABLE MonthlyEmployeeMetrics (
            month_year NVARCHAR(7),
            employee_state NVARCHAR(20),
            employee_id INT,
            unique_customers_serviced INT,
            total_products_sold INT,
            total_money_made DECIMAL(18, 2)
            -- Optionally add avg_money_spent_per_order/product
        );

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
