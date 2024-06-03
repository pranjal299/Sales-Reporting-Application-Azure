CREATE PROCEDURE DQCheck_Validation_Customers
AS
BEGIN
-- Remove rows with missing values from Customers
    DELETE FROM Customers
    WHERE customer_id IS NULL 
    OR [customer_email] IS NULL 
    OR customer_first_name IS NULL 
    OR customer_last_name IS NULL 
    OR customer_phone IS NULL
    OR customer_postal IS NULL
    OR customer_state IS NULL;

-- Remove duplicate rows from Customer
    DELETE FROM Customers
    WHERE customer_id IN (
        SELECT customer_id
        FROM (
            SELECT customer_id, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY customer_id) AS row_num
            FROM Customers
        ) AS temp
        WHERE temp.row_num > 1
    );
    
END;
GO