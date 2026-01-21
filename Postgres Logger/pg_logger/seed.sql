-- PostgreSQL Log Streamer - Test Database Seed
-- Creates sample tables and data for testing

-- Create test tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test users
INSERT INTO users (username, email, active) VALUES
    ('alice', 'alice@example.com', true),
    ('bob', 'bob@example.com', true),
    ('charlie', 'charlie@example.com', false),
    ('diana', 'diana@example.com', true),
    ('eve', 'eve@example.com', true);

-- Insert test products
INSERT INTO products (name, price, category, stock) VALUES
    ('Laptop', 999.99, 'Electronics', 50),
    ('Mouse', 24.99, 'Electronics', 200),
    ('Keyboard', 79.99, 'Electronics', 150),
    ('Monitor', 299.99, 'Electronics', 75),
    ('Desk Chair', 199.99, 'Furniture', 30),
    ('Notebook', 4.99, 'Stationery', 500),
    ('Pen Set', 12.99, 'Stationery', 300),
    ('Backpack', 49.99, 'Accessories', 100);

-- Insert test orders
INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES
    (1, 1, 1, 999.99),
    (1, 2, 2, 49.98),
    (2, 3, 1, 79.99),
    (3, 4, 1, 299.99),
    (4, 5, 1, 199.99),
    (5, 6, 10, 49.90),
    (1, 7, 5, 64.95),
    (2, 8, 1, 49.99);

-- Create indexes for testing
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Create a test function
CREATE OR REPLACE FUNCTION get_user_order_count(user_name VARCHAR)
RETURNS INT AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE u.username = user_name
    );
END;
$$ LANGUAGE plpgsql;

-- Create a view for testing
CREATE OR REPLACE VIEW user_order_summary AS
SELECT 
    u.username,
    u.email,
    COUNT(o.id) as order_count,
    COALESCE(SUM(o.total_price), 0) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username, u.email;

-- Grant permissions (already postgres superuser, but good practice)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Output success message
DO $$
BEGIN
    RAISE NOTICE 'Test database seeded successfully!';
    RAISE NOTICE 'Tables: users (% rows), products (% rows), orders (% rows)',
        (SELECT COUNT(*) FROM users),
        (SELECT COUNT(*) FROM products),
        (SELECT COUNT(*) FROM orders);
END $$;
