
    CREATE TABLE Transactions (
        transaction_id INT PRIMARY KEY,
        timestamp DATETIME,
        customer_id INT,
        product_id INT,
        employee_id INT,
        payment_id INT,
        quantity INT,
        total_amount DECIMAL(10, 2),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES Products(product_id),
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
        FOREIGN KEY (payment_id) REFERENCES Payments(payment_id)
    );
    