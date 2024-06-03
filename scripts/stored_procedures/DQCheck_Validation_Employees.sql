
CREATE PROCEDURE DQCheck_Validation_Employees
AS
BEGIN
-- Remove rows with missing values from Employees
    DELETE FROM Employees
    WHERE employee_id IS NULL 
    OR employee_city IS NULL 
    OR employee_name IS NULL 
    OR employee_phone IS NULL 
    OR employee_postal IS NULL
    OR employee_ssn IS NULL
    OR employee_state IS NULL;

-- Remove duplicate rows from Employees
    DELETE FROM Employees
    WHERE employee_id IN (
        SELECT employee_id
        FROM (
            SELECT employee_id, ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY employee_id) AS row_num
            FROM Employees
        ) AS temp
        WHERE temp.row_num > 1
    );
    
END;
GO