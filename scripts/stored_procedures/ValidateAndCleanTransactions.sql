-- Example: Stored Procedure to Validate and Clean Transactions Data
CREATE PROCEDURE ValidateAndCleanTransactions
AS
BEGIN
    -- Example: Remove rows with missing or invalid data
    DELETE FROM Transactions
    WHERE [transaction_id] IS NULL OR [timestamp] IS NULL OR total_amount IS NULL 
    OR customer_id IS NULL OR product_id IS NULL OR employee_id IS NULL 
    OR total_amount < 0 OR total_amount > 1000000;

END;
GO