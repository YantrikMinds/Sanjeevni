/**
 * SANJEEVNI - Configuration & Regional Presets
 */
const CONFIG = {
  OWM_KEY: 'd76a872e70fbf69f3f686b6db59c4f09',
  TINYFISH_KEY: 'sk-tinyfish-twKoGbUhuazG6n7nwig9k9gHfeRZiMbw',
  DEFAULT_CITY: 'Noida',
  DEFAULT_LAT: 28.5800,
  DEFAULT_LNG: 77.3300,
  OSRM_BASE: 'https://router.project-osrm.org/route/v1/driving',
  NOMINATIM_BASE: 'https://nominatim.openstreetmap.org/search',
  USGS_BASE: 'https://earthquake.usgs.gov/fdsnws/event/1/query'
};

const DEMO = {
  hospitals: [
    { name: 'Kailash Hospital & Heart Institute', lat: 28.5833, lng: 77.3333, icu: 18, total_icu: 30, ventilators: 14, blood_units: 14, distance_km: 2.5, time_min: 10, address: 'Sector 27, Noida', status: 'Operational', o2: '98%' },
    { name: 'Fortis Hospital Noida', lat: 28.6186, lng: 77.3725, icu: 0, total_icu: 25, ventilators: 2, blood_units: 3, distance_km: 7.4, time_min: 18, address: 'Sector 62, Noida', status: 'Full Capacity', o2: '82%' },
    { name: 'Metro Hospital & Heart Institute', lat: 28.5950, lng: 77.3350, icu: 9, total_icu: 15, ventilators: 6, blood_units: 8, distance_km: 3.8, time_min: 12, address: 'Sector 11, Noida', status: 'Operational', o2: '92%' },
    { name: 'Jaypee Hospital', lat: 28.5140, lng: 77.3710, icu: 22, total_icu: 40, ventilators: 16, blood_units: 20, distance_km: 11.2, time_min: 24, address: 'Sector 128, Noida', status: 'Operational', o2: '96%' },
    { name: 'AIIMS New Delhi', lat: 28.5668, lng: 77.2078, icu: 35, total_icu: 60, ventilators: 28, blood_units: 32, distance_km: 18.5, time_min: 28, address: 'Ansari Nagar, New Delhi', status: 'Operational', o2: '99%' }
  ],
  alerts: [
    { id: 1, type: 'road', title: 'Sector 95 Underpass Waterlogged', desc: 'Water level 1.1m above deck. Traffic diverted to elevated arterial bypass.', severity: 'high', time: 'Today, 10:15 AM', location: 'Sector 95 Noida Corridor', lat: 28.5450, lng: 77.3400 },
    { id: 2, type: 'road', title: 'Expressway Flyover Congestion Alert', desc: 'Emergency utility repairs underway along inner ring road. Use alternate route.', severity: 'medium', time: 'Today, 08:42 AM', location: 'DND / Noida Expressway', lat: 28.5700, lng: 77.3100 },
    { id: 3, type: 'flood', title: 'Yamuna Floodplain Runoff Advisory', desc: 'Low-lying sectors on flood watch due to upstream water release.', severity: 'medium', time: '12 mins ago', location: 'Noida-Delhi Border', lat: 28.5600, lng: 77.3050 },
    { id: 4, type: 'earthquake', title: 'M 3.8 Seismic Tremor', desc: 'Depth 12km. Slight tremor recorded along regional fault zone.', severity: 'medium', time: '2 hours ago', location: 'Northern Seismic Fault', lat: 28.8955, lng: 76.6066 }
  ],
  weather: {
    temp: 24,
    desc: 'Clear Sky',
    humidity: 52,
    wind: 12,
    pressure: 1014,
    visibility: 8,
    city: 'Noida',
    high: 28,
    low: 18,
    icon: '01d'
  },
  forecast: [
    { day: 'Today', high: 28, low: 18, icon: '☀️', desc: 'Sunny' },
    { day: 'Sun', high: 27, low: 17, icon: '⛅', desc: 'Partly Cloudy' },
    { day: 'Mon', high: 29, low: 18, icon: '🌤️', desc: 'Clear' },
    { day: 'Tue', high: 26, low: 16, icon: '🌧️', desc: 'Light Showers' },
    { day: 'Wed', high: 28, low: 17, icon: '⛅', desc: 'Hazy' },
    { day: 'Thu', high: 27, low: 17, icon: '🌤️', desc: 'Mild' },
    { day: 'Fri', high: 26, low: 16, icon: '☀️', desc: 'Clear' }
  ],
  earthquakes: [
    { mag: 3.4, place: 'Rohtak Fault, Haryana', time: '2 hours ago | 10 km depth', lat: 28.8955, lng: 76.6066, depth: 10, distanceKm: 85, proximityText: '⚠️ 85 km from you (Close)' },
    { mag: 4.1, place: 'Garhwal Thrust, Uttarakhand', time: '4 hours ago | 15 km depth', lat: 30.5500, lng: 78.4000, depth: 15, distanceKm: 240, proximityText: '240 km from your location' },
    { mag: 2.9, place: 'Alwar-Delhi Shear Zone', time: '6 hours ago | 8 km depth', lat: 27.8500, lng: 76.7000, depth: 8, distanceKm: 110, proximityText: '⚠️ 110 km from you (Close)' },
    { mag: 4.6, place: 'Western Nepal Border', time: '8 hours ago | 25 km depth', lat: 29.2000, lng: 81.1000, depth: 25, distanceKm: 380, proximityText: '380 km from your location' }
  ],
  routes: {
    originalRoute: [
      [28.5800, 77.3300],
      [28.5820, 77.3320],
      [28.5833, 77.3333]
    ],
    detourRoute: [
      [28.5800, 77.3300],
      [28.5850, 77.3310],
      [28.5833, 77.3333]
    ]
  }
};
