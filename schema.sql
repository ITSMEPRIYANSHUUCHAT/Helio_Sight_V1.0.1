-- Revamped SQL Schema for RayVolt Dashboard (Helio Sight V1.0.1)
-- Production-ready: RLS roles created first, hypertables after tables, compression/retention.
-- Comment DROP for prod to avoid wipe. Run once via pgAdmin or initdb.

-- Drop existing (for dev reset; comment in prod)
DROP MATERIALIZED VIEW IF EXISTS customer_metrics;
DROP TABLE IF EXISTS error_logs CASCADE;
DROP TABLE IF EXISTS device_data_historical CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS fault_logs CASCADE;
DROP TABLE IF EXISTS weather_data CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS plants CASCADE;
DROP TABLE IF EXISTS api_credentials CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS api_provider_type CASCADE;
DROP TYPE IF EXISTS severity_type CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
DROP ROLE IF EXISTS customer CASCADE;
DROP ROLE IF EXISTS installer CASCADE;

-- Create ENUM types
CREATE TYPE api_provider_type AS ENUM ('shinemonitor', 'solarman', 'soliscloud', 'other');
CREATE TYPE severity_type AS ENUM ('low', 'medium', 'high');

-- Create roles for RLS (before tables)
CREATE ROLE customer NOLOGIN;
CREATE ROLE installer NOLOGIN;

-- Create users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'),
    password_hash TEXT NOT NULL,
    usertype TEXT NOT NULL CHECK (usertype IN ('customer', 'installer')),
    profile JSONB NOT NULL DEFAULT '{}',
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_usertype ON users(usertype);

-- Enable RLS on users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_policy ON users
    USING (id = current_setting('app.current_user_id')::TEXT)
    WITH CHECK (id = current_setting('app.current_user_id')::TEXT);
CREATE POLICY installer_user_policy ON users FOR ALL
    TO installer
    USING (true);

-- Insert demo users and grant roles
INSERT INTO users (id, username, name, email, password_hash, usertype, profile, verified)
VALUES 
    ('507f1f77bcf86cd799439011', 'demo', 'Demo User', 'demo@example.com', '$2b$12$mcZLDV4fPyhoKsGIUyk03eQxkANE0ifIFYJpITZAAb1s61BE.Z9Oe', 'customer', '{"installationId": "INST-12345", "address": "123 Solar Street, CA", "whatsappNumber": "+1234567890"}', TRUE),
    ('507f1f77bcf86cd799439012', 'admin', 'Admin User', 'admin@example.com', '$2b$12$b4Dp/13Bh2bN/5nlpKxBrer3sN0zRxrnSPlEk7Ex8lKlNGog6eedu', 'installer', '{"companyName": "Solar Install Co", "licenseNumber": "LIC-789", "phoneNumber": "+1-555-0123", "panelBrand": "SunPower", "panelCapacity": 5.0, "panelType": "monocrystalline", "inverterBrand": "SMA", "inverterCapacity": 4.0, "whatsappNumber": "+1987654321"}', TRUE);

GRANT customer TO "507f1f77bcf86cd799439011";
GRANT installer TO "507f1f77bcf86cd799439012";

-- Create customers table
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    email TEXT CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'),
    phone TEXT,
    address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_email ON customers(email);

-- Enable RLS on customers
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
CREATE POLICY customer_policy ON customers
    USING (user_id = current_setting('app.current_user_id')::TEXT);
CREATE POLICY installer_customer_policy ON customers FOR ALL
    TO installer
    USING (true);

-- Create api_credentials table
CREATE TABLE api_credentials (
    credential_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    api_provider api_provider_type NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    api_key TEXT,
    api_secret TEXT,
    last_fetched TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);
CREATE INDEX idx_api_credentials_customer_id ON api_credentials(customer_id);
CREATE INDEX idx_api_credentials_api_provider ON api_credentials(api_provider);
CREATE INDEX idx_api_credentials_user_id ON api_credentials(user_id);
CREATE INDEX idx_api_credentials_last_fetched ON api_credentials(last_fetched DESC);

-- Enable RLS on api_credentials
ALTER TABLE api_credentials ENABLE ROW LEVEL SECURITY;
CREATE POLICY cred_policy ON api_credentials
    USING (customer_id = (SELECT customer_id FROM customers WHERE user_id = current_setting('app.current_user_id')::TEXT));

-- Create plants table
CREATE TABLE plants (
    plant_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    plant_name TEXT NOT NULL,
    capacity DOUBLE PRECISION CHECK (capacity >= 0 AND capacity <= 100000),
    total_energy DOUBLE PRECISION CHECK (total_energy >= 0),
    install_date DATE,
    location TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);
CREATE INDEX idx_plants_customer_id ON plants(customer_id);
CREATE INDEX idx_plants_install_date ON plants(install_date);

-- Enable RLS on plants
ALTER TABLE plants ENABLE ROW LEVEL SECURITY;
CREATE POLICY plant_policy ON plants
    USING (customer_id = current_setting('app.current_customer_id')::TEXT);

-- Create devices table
CREATE TABLE devices (
    device_sn TEXT PRIMARY KEY,
    plant_id TEXT NOT NULL,
    inverter_model TEXT,
    panel_model TEXT,
    pv_count INTEGER CHECK (pv_count >= 0 AND pv_count <= 100),
    string_count INTEGER CHECK (string_count >= 0 AND string_count <= 20),
    first_install_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
);
CREATE INDEX idx_devices_plant_id ON devices(plant_id);
CREATE INDEX idx_devices_inverter_model ON devices(inverter_model);

-- Enable RLS on devices
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
CREATE POLICY device_policy ON devices
    USING (plant_id IN (SELECT plant_id FROM plants WHERE customer_id = current_setting('app.current_customer_id')::TEXT));

-- Create weather_data table
CREATE TABLE weather_data (
    plant_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION CHECK (temperature >= -50 AND temperature <= 60),
    irradiance DOUBLE PRECISION CHECK (irradiance >= 0 AND irradiance <= 1500),
    humidity DOUBLE PRECISION CHECK (humidity >= 0 AND humidity <= 100),
    wind_speed DOUBLE PRECISION CHECK (wind_speed >= 0 AND wind_speed <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE,
    PRIMARY KEY (plant_id, timestamp)
);
-- FIXED: Hypertable AFTER table
SELECT create_hypertable('weather_data', 'timestamp', if_not_exists => TRUE);
ALTER TABLE weather_data SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'timestamp DESC',
    timescaledb.compress_segmentby = 'plant_id'
);
SELECT add_compression_policy('weather_data', INTERVAL '7 days');
SELECT add_retention_policy('weather_data', INTERVAL '2 years');
CREATE INDEX idx_weather_data_plant_id_timestamp ON weather_data (plant_id, timestamp DESC);

-- Enable RLS on weather_data
ALTER TABLE weather_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY weather_policy ON weather_data
    USING (plant_id IN (SELECT plant_id FROM plants WHERE customer_id = current_setting('app.current_customer_id')::TEXT));

-- Create device_data_historical table
CREATE TABLE device_data_historical (
    device_sn TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    pv01_voltage DOUBLE PRECISION CHECK (pv01_voltage >= 0 AND pv01_voltage <= 1000),
    pv01_current DOUBLE PRECISION CHECK (pv01_current >= 0 AND pv01_current <= 20),
    pv02_voltage DOUBLE PRECISION CHECK (pv02_voltage >= 0 AND pv02_voltage <= 1000),
    pv02_current DOUBLE PRECISION CHECK (pv02_current >= 0 AND pv02_current <= 20),
    pv03_voltage DOUBLE PRECISION CHECK (pv03_voltage >= 0 AND pv03_voltage <= 1000),
    pv03_current DOUBLE PRECISION CHECK (pv03_current >= 0 AND pv03_current <= 20),
    pv04_voltage DOUBLE PRECISION CHECK (pv04_voltage >= 0 AND pv04_voltage <= 1000),
    pv04_current DOUBLE PRECISION CHECK (pv04_current >= 0 AND pv04_current <= 20),
    pv05_voltage DOUBLE PRECISION CHECK (pv05_voltage >= 0 AND pv05_voltage <= 1000),
    pv05_current DOUBLE PRECISION CHECK (pv05_current >= 0 AND pv05_current <= 20),
    pv06_voltage DOUBLE PRECISION CHECK (pv06_voltage >= 0 AND pv06_voltage <= 1000),
    pv06_current DOUBLE PRECISION CHECK (pv06_current >= 0 AND pv06_current <= 20),
    pv07_voltage DOUBLE PRECISION CHECK (pv07_voltage >= 0 AND pv07_voltage <= 1000),
    pv07_current DOUBLE PRECISION CHECK (pv07_current >= 0 AND pv07_current <= 20),
    pv08_voltage DOUBLE PRECISION CHECK (pv08_voltage >= 0 AND pv08_voltage <= 1000),
    pv08_current DOUBLE PRECISION CHECK (pv08_current >= 0 AND pv08_current <= 20),
    pv09_voltage DOUBLE PRECISION CHECK (pv09_voltage >= 0 AND pv09_voltage <= 1000),
    pv09_current DOUBLE PRECISION CHECK (pv09_current >= 0 AND pv09_current <= 20),
    pv10_voltage DOUBLE PRECISION CHECK (pv10_voltage >= 0 AND pv10_voltage <= 1000),
    pv10_current DOUBLE PRECISION CHECK (pv10_current >= 0 AND pv10_current <= 20),
    pv11_voltage DOUBLE PRECISION CHECK (pv11_voltage >= 0 AND pv11_voltage <= 1000),
    pv11_current DOUBLE PRECISION CHECK (pv11_current >= 0 AND pv11_current <= 20),
    pv12_voltage DOUBLE PRECISION CHECK (pv12_voltage >= 0 AND pv12_voltage <= 1000),
    pv12_current DOUBLE PRECISION CHECK (pv12_current >= 0 AND pv12_current <= 20),
    r_voltage DOUBLE PRECISION CHECK (r_voltage >= 0 AND r_voltage <= 325),
    s_voltage DOUBLE PRECISION CHECK (s_voltage >= 0 AND s_voltage <= 325),
    t_voltage DOUBLE PRECISION CHECK (t_voltage >= 0 AND t_voltage <= 325),
    r_current DOUBLE PRECISION CHECK (r_current >= 0 AND r_current <= 500),
    s_current DOUBLE PRECISION CHECK (s_current >= 0 AND s_current <= 500),
    t_current DOUBLE PRECISION CHECK (t_current >= 0 AND t_current <= 500),
    rs_voltage DOUBLE PRECISION CHECK (rs_voltage >= 0 AND rs_voltage <= 500),
    st_voltage DOUBLE PRECISION CHECK (st_voltage >= 0 AND st_voltage <= 500),
    tr_voltage DOUBLE PRECISION CHECK (tr_voltage >= 0 AND tr_voltage <= 500),
    frequency DOUBLE PRECISION CHECK (frequency >= 45 AND frequency <= 65),
    total_power DOUBLE PRECISION CHECK (total_power >= 0 AND total_power <= 100000),
    reactive_power DOUBLE PRECISION CHECK (reactive_power >= -100000 AND reactive_power <= 100000),
    energy_today DOUBLE PRECISION CHECK (energy_today >= 0 AND energy_today <= 20000),
    cuf DOUBLE PRECISION CHECK (cuf >= 0 AND cuf <= 100),
    pr DOUBLE PRECISION CHECK (pr >= 0 AND pr <= 100),
    state TEXT CHECK (state IN ('online', 'offline', 'maintenance', 'faulty', 'unknown')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (device_sn) REFERENCES devices(device_sn) ON DELETE CASCADE,
    PRIMARY KEY (device_sn, timestamp)
);
-- FIXED: Hypertable AFTER table
SELECT create_hypertable('device_data_historical', 'timestamp', if_not_exists => TRUE);
ALTER TABLE device_data_historical SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'timestamp DESC',
    timescaledb.compress_segmentby = 'device_sn'
);
SELECT add_compression_policy('device_data_historical', INTERVAL '7 days');
SELECT add_retention_policy('device_data_historical', INTERVAL '2 years');
CREATE INDEX idx_device_data_historical_device_sn_timestamp ON device_data_historical (device_sn, timestamp DESC);
CREATE INDEX idx_device_data_historical_total_power ON device_data_historical (total_power) WHERE total_power > 0;

-- Enable RLS
ALTER TABLE device_data_historical ENABLE ROW LEVEL SECURITY;
CREATE POLICY data_policy ON device_data_historical
    USING (device_sn IN (SELECT device_sn FROM devices d JOIN plants p ON d.plant_id = p.plant_id WHERE p.customer_id = current_setting('app.current_customer_id')::TEXT));

-- Create predictions table
CREATE TABLE predictions (
    prediction_id SERIAL NOT NULL,
    device_sn TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    predicted_energy DOUBLE PRECISION CHECK (predicted_energy >= 0),
    predicted_pr DOUBLE PRECISION CHECK (predicted_pr >= 0 AND predicted_pr <= 100),
    confidence_score DOUBLE PRECISION CHECK (confidence_score >= 0 AND confidence_score <= 1),
    model_version TEXT NOT NULL CHECK (model_version ~ '^v[0-9]+\.[0-9]+$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (device_sn) REFERENCES devices(device_sn) ON DELETE CASCADE,
    PRIMARY KEY (prediction_id, timestamp)
);
-- FIXED: Hypertable AFTER table
SELECT create_hypertable('predictions', 'timestamp', if_not_exists => TRUE);
ALTER TABLE predictions SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'timestamp DESC',
    timescaledb.compress_segmentby = 'device_sn'
);
SELECT add_compression_policy('predictions', INTERVAL '7 days');
SELECT add_retention_policy('predictions', INTERVAL '2 years');
CREATE INDEX idx_predictions_device_sn_timestamp ON predictions (device_sn, timestamp DESC);

-- Enable RLS
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY pred_policy ON predictions
    USING (device_sn IN (SELECT device_sn FROM devices d JOIN plants p ON d.plant_id = p.plant_id WHERE p.customer_id = current_setting('app.current_customer_id')::TEXT));

-- Create fault_logs table
CREATE TABLE fault_logs (
    fault_id SERIAL NOT NULL,
    device_sn TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    fault_code TEXT NOT NULL,
    fault_description TEXT,
    severity severity_type,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    FOREIGN KEY (device_sn) REFERENCES devices(device_sn) ON DELETE CASCADE,
    PRIMARY KEY (fault_id, timestamp)
);
-- FIXED: Hypertable AFTER table
SELECT create_hypertable('fault_logs', 'timestamp', if_not_exists => TRUE);
ALTER TABLE fault_logs SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'timestamp DESC',
    timescaledb.compress_segmentby = 'device_sn'
);
SELECT add_compression_policy('fault_logs', INTERVAL '7 days');
SELECT add_retention_policy('fault_logs', INTERVAL '2 years');
CREATE INDEX idx_fault_logs_device_sn_timestamp ON fault_logs (device_sn, timestamp DESC);
CREATE INDEX idx_fault_logs_severity ON fault_logs (severity);

-- Enable RLS
ALTER TABLE fault_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY fault_policy ON fault_logs
    USING (device_sn IN (SELECT device_sn FROM devices d JOIN plants p ON d.plant_id = p.plant_id WHERE p.customer_id = current_setting('app.current_customer_id')::TEXT));

-- Create error_logs table
CREATE TABLE error_logs (
    error_id SERIAL NOT NULL,
    customer_id TEXT,
    device_sn TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    api_provider api_provider_type,
    field_name TEXT,
    field_value TEXT,
    error_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    PRIMARY KEY (error_id, timestamp)
);
-- FIXED: Hypertable AFTER table
SELECT create_hypertable('error_logs', 'timestamp', if_not_exists => TRUE);
ALTER TABLE error_logs SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'timestamp DESC',
    timescaledb.compress_segmentby = 'customer_id'
);
SELECT add_compression_policy('error_logs', INTERVAL '7 days');
SELECT add_retention_policy('error_logs', INTERVAL '1 year');
CREATE INDEX idx_error_logs_customer_id_timestamp ON error_logs (customer_id, timestamp DESC);

-- Enable RLS
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY error_policy ON error_logs
    USING (customer_id = current_setting('app.current_customer_id')::TEXT);

-- Continuous aggregate for customer_metrics (after tables)
CREATE MATERIALIZED VIEW customer_metrics WITH (timescaledb.continuous) AS
SELECT 
    p.customer_id,
    time_bucket('1 day', ddh.timestamp) AS day,
    SUM(ddh.energy_today) AS total_energy_today,
    AVG(ddh.pr) AS avg_pr,
    COUNT(DISTINCT d.device_sn) AS active_devices
FROM device_data_historical ddh
JOIN devices d ON ddh.device_sn = d.device_sn
JOIN plants p ON d.plant_id = p.plant_id
WHERE ddh.total_power > 0
GROUP BY p.customer_id, day;
SELECT add_continuous_aggregate_policy('customer_metrics',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour');

-- Trigger function (unchanged)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers (with WHEN for soft delete)
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_credentials_updated_at BEFORE UPDATE ON api_credentials FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_plants_updated_at BEFORE UPDATE ON plants FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_weather_data_updated_at BEFORE UPDATE ON weather_data FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_device_data_historical_updated_at BEFORE UPDATE ON device_data_historical FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fault_logs_updated_at BEFORE UPDATE ON fault_logs FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_error_logs_updated_at BEFORE UPDATE ON error_logs FOR EACH ROW WHEN (NEW.deleted_at IS NULL) EXECUTE FUNCTION update_updated_at_column();

-- Procedure for soft delete (unchanged)
CREATE OR REPLACE PROCEDURE soft_delete_customer(cust_id TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE customers SET deleted_at = NOW() WHERE customer_id = cust_id;
    UPDATE plants SET deleted_at = NOW() WHERE customer_id = cust_id;
    UPDATE devices SET deleted_at = NOW() WHERE plant_id IN (SELECT plant_id FROM plants WHERE customer_id = cust_id);
END;
$$;

-- View for active data (unchanged)
CREATE VIEW active_device_data AS
SELECT * FROM device_data_historical WHERE deleted_at IS NULL;