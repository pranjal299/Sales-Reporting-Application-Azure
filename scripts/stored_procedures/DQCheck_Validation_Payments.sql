CREATE PROCEDURE DQCheck_Validation_Payments
AS
BEGIN
-- Remove rows with missing values from Payments
    DELETE FROM Payments
    WHERE payment_id IS NULL 
    OR [payment_type] IS NULL;

-- Remove duplicate rows from Products
    DELETE FROM Payments
    WHERE payment_id IN (
        SELECT payment_id
        FROM (
            SELECT payment_id, ROW_NUMBER() OVER (PARTITION BY payment_id ORDER BY payment_id) AS row_num
            FROM Payments
        ) AS temp
        WHERE temp.row_num > 1
    );

END;
GO