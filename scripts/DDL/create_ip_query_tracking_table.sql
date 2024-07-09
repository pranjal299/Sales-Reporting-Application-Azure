CREATE TABLE IPQueryTracking (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    query_count INT NOT NULL DEFAULT 0,
    last_query_date DATE NOT NULL,
    CONSTRAINT UQ_IPAddress UNIQUE (ip_address)
);