CREATE TABLE IPQueryTracking (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ip_address VARCHAR(15) NOT NULL,  -- Changed to VARCHAR(15) to store only the IP without port
    query_count INT NOT NULL DEFAULT 0,
    last_query_date DATE NOT NULL,
    CONSTRAINT UQ_IPAddress UNIQUE (ip_address)
);