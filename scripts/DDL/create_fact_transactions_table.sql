
    CREATE TABLE Transactions (
        transaction_id INT PRIMARY KEY,
        timestamp DATETIME,
        customer_id INT,
        product_id INT,
        employee_id INT,
        payment_id INT,
        quantity INT,
        total_amount DECIMAL(10, 2),
    );
    