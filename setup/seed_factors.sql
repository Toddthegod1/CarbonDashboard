INSERT INTO emissions_factors (category, unit, kg_co2e_per_unit) VALUES
('electricity_nz', 'kWh', 0.097),         -- illustrative value
('car_gasoline', 'km', 0.192),            -- avg passenger vehicle per km (illustrative)
('natural_gas', 'kWh', 0.183),            -- illustrative
('flight_shorthaul', 'km', 0.158),        -- illustrative
('beef', 'kg', 27.0)                      -- illustrative
ON CONFLICT DO NOTHING;