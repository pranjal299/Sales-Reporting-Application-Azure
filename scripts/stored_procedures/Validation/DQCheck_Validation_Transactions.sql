CREATE PROCEDURE DQCheck_Validation_Transactions
AS
BEGIN
-- Remove rows with missing values from Transactions
    DELETE FROM Transactions
    WHERE transaction_id IS NULL 
    OR [timestamp] IS NULL 
    OR total_amount IS NULL 
    OR customer_id IS NULL 
    OR product_id IS NULL
    OR employee_id IS NULL
    OR payment_id IS NULL;

-- Remove duplicate rows from Transactions
    DELETE FROM Transactions
    WHERE transaction_id IN (
        SELECT transaction_id
        FROM (
            SELECT transaction_id, ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_id) AS row_num
            FROM Transactions
        ) AS temp
        WHERE temp.row_num > 1
    );

-- Remove invalid rows from Transactions
    DELETE FROM Transactions
    WHERE TRY_CAST([timestamp] AS DATE) IS NULL OR TRY_CAST(total_amount AS DECIMAL(18, 2)) IS NULL 
    OR total_amount < 0  
    OR payment_id NOT IN (SELECT payment_id FROM Payments) 
    OR product_id NOT IN (SELECT product_id FROM Products) 
    OR customer_id NOT IN (SELECT customer_id FROM Customers)
    OR employee_id NOT IN (SELECT employee_id FROM Employees);

END;
GO