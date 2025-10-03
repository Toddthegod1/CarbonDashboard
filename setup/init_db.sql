CREATE TABLE IF NOT EXISTS emissions_factors (
  id SERIAL PRIMARY KEY,
  category VARCHAR(64) NOT NULL,            -- e.g., "electricity", "car_gasoline", "natural_gas"
  unit VARCHAR(32) NOT NULL,                -- e.g., "kWh", "km", "kg", "L"
  kg_co2e_per_unit NUMERIC(12,6) NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
  id SERIAL PRIMARY KEY,
  ts TIMESTAMP NOT NULL DEFAULT NOW(),
  category VARCHAR(64) NOT NULL,
  amount NUMERIC(14,4) NOT NULL,
  unit VARCHAR(32) NOT NULL,
  note TEXT,
  kg_co2e NUMERIC(14,6) NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
  id SERIAL PRIMARY KEY,
  period_month INTEGER NOT NULL,            -- 1..12
  period_year INTEGER NOT NULL,             -- e.g., 2025
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING',  -- PENDING, COMPLETE, ERROR
  s3_key TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_period ON reports(period_month, period_year);