-- Create tables for Air Quality and ISPA Monitoring

-- 1. Reference table for Cities
CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    UNIQUE(name)
);

-- Seed Central Java cities (Coordinates are approximate for city centers)
INSERT INTO cities (name, latitude, longitude) VALUES
('KEBUMEN', -7.6685, 109.6543),
('PATI', -6.7556, 111.0380),
('BREBES', -6.8706, 109.0369),
('TEGAL', -6.8694, 109.1402),
('DEMAK', -6.8948, 110.6386),
('BANJARNEGARA', -7.3999, 109.6974),
('KARANGANYAR', -7.5990, 110.9506),
('KOTA SEMARANG', -7.0051, 110.4381),
('KLATEN', -7.7025, 110.6029),
('PURBALINGGA', -7.3932, 109.3629),
('KUDUS', -6.8048, 110.8405),
('WONOSOBO', -7.3632, 109.9001),
('CILACAP', -7.7188, 109.0159),
('JEPARA', -6.5818, 110.6784),
('GROBOGAN', -7.0266, 110.9229),
('SUKOHARJO', -7.6044, 110.8166),
('SEMARANG', -7.1434, 110.4072), -- Kabupaten Semarang
('TEMANGGUNG', -7.3132, 110.1727),
('BANYUMAS', -7.5155, 109.2944),
('BOYOLALI', -7.5380, 110.5966),
('PEMALANG', -6.8910, 109.3807),
('MAGELANG', -7.4336, 110.2177), -- Kabupaten Magelang
('KENDAL', -6.9189, 110.2038),
('KOTA TEGAL', -6.8673, 109.1384),
('BLORA', -6.9698, 111.4184),
('REMBANG', -6.7114, 111.3451),
('KOTA SURAKARTA', -7.5755, 110.8243),
('PEKALONGAN', -6.8898, 109.6746), -- Kabupaten Pekalongan
('WONOGIRI', -7.8180, 110.9213),
('KOTA PEKALONGAN', -6.8886, 109.6753),
('KOTA MAGELANG', -7.4706, 110.2178),
('SRAGEN', -7.4275, 111.0225),
('KOTA SALATIGA', -7.3305, 110.5084),
('PURWOREJO', -7.7156, 110.0093),
('BATANG', -6.9135, 109.7285)
ON CONFLICT (name) DO NOTHING;

-- 2. Weather and Air Quality Log (Time-series data)
CREATE TABLE IF NOT EXISTS weather_log (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    timestamp TIMESTAMP NOT NULL,
    temperature_c DECIMAL(5,2),
    humidity_percent DECIMAL(5,2),
    wind_speed_kmh DECIMAL(5,2),
    weather_condition VARCHAR(50),
    wind_direction DECIMAL(5,2),
    uv_index DECIMAL(4,2),
    pollution_index INTEGER, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. ISPA Cases (Yearly/Aggregated)
-- Modified to match the CSV structure which seems to be yearly (2023)
CREATE TABLE IF NOT EXISTS ispa_cases (
    id SERIAL PRIMARY KEY,
    city_id INTEGER REFERENCES cities(id),
    report_year INTEGER NOT NULL,
    pneumonia_cases DECIMAL(10,3), -- Using decimal as CSV has dots, might be thousands or decimals. Assuming thousands based on context but will check.
    ispa_cases DECIMAL(12,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city_id, report_year)
);
