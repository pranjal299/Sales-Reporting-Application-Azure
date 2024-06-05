CREATE PROCEDURE DQCheck_Validation_Products
AS
BEGIN
-- Remove rows with missing values from Products
    DELETE FROM Products
    WHERE product_id IS NULL 
    OR [product_name] IS NULL 
    OR product_category IS NULL 
    OR unit_price IS NULL;

-- Remove duplicate rows from Products
    DELETE FROM Products
    WHERE product_id IN (
        SELECT product_id
        FROM (
            SELECT product_id, ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY product_id) AS row_num
            FROM Products
        ) AS temp
        WHERE temp.row_num > 1
    );

-- Remove invalid rows from Products
    DELETE FROM Products
    WHERE TRY_CAST(unit_price AS DECIMAL(18, 2)) IS NULL 
    OR unit_price < 0;

END;
GO