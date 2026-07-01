/* ═══════════════════════════════════════════════════════════════════
   CityRegistry — City seed data loader and query engine
   ═══════════════════════════════════════════════════════════════════
   Loads city data from seed-data/earth/cities/ and provides
   lookup by name, region, uCode, or GPS coordinates.
   ═══════════════════════════════════════════════════════════════════ */

import { latLonToUCode, distanceBetween } from './SpatialCodec'

export interface CityMarker {
  name: string
  lat: number
  lon: number
  uCode: string
  timezone: string
  population: number
  landmark: string
  tags: string[]
  region: string
  teletextPage?: number
}

export interface RegionData {
  region: string
  layer: number
  cities: CityMarker[]
}

// ─── Built-in city data (embedded for browser use) ────────────────────

const BUILTIN_CITIES: RegionData[] = [
  {
    region: 'oceania',
    layer: 340,
    cities: [
      { name: 'Sydney', lat: -33.8688, lon: 151.2093, uCode: 'L340-H42J-08F2-0', timezone: 'Australia/Sydney', population: 5300000, landmark: 'Sydney Opera House', tags: ['coastal', 'harbour', 'financial'], region: 'oceania' },
      { name: 'Melbourne', lat: -37.8136, lon: 144.9631, uCode: 'L340-H42J-0C1C-0', timezone: 'Australia/Melbourne', population: 5000000, landmark: 'Federation Square', tags: ['cultural', 'sports', 'arts'], region: 'oceania' },
      { name: 'Brisbane', lat: -27.4698, lon: 153.0251, uCode: 'L340-H42J-0A1G-0', timezone: 'Australia/Brisbane', population: 2500000, landmark: 'South Bank Parklands', tags: ['subtropical', 'river', 'outdoor'], region: 'oceania' },
      { name: 'Perth', lat: -31.9505, lon: 115.8605, uCode: 'L340-H42I-0E0M-0', timezone: 'Australia/Perth', population: 2100000, landmark: 'Kings Park', tags: ['isolated', 'beach', 'mining'], region: 'oceania' },
      { name: 'Adelaide', lat: -34.9285, lon: 138.6007, uCode: 'L340-H42J-0A0O-0', timezone: 'Australia/Adelaide', population: 1300000, landmark: 'Adelaide Oval', tags: ['wine', 'festival', 'parklands'], region: 'oceania' },
      { name: 'Auckland', lat: -36.8485, lon: 174.7633, uCode: 'L340-H42K-0E1A-0', timezone: 'Pacific/Auckland', population: 1600000, landmark: 'Sky Tower', tags: ['harbour', 'volcanic', 'sailing'], region: 'oceania' },
      { name: 'Wellington', lat: -41.2865, lon: 174.7762, uCode: 'L340-H42K-0G0G-0', timezone: 'Pacific/Auckland', population: 420000, landmark: 'Te Papa Museum', tags: ['capital', 'windy', 'creative'], region: 'oceania' },
      { name: 'Christchurch', lat: -43.5320, lon: 172.6306, uCode: 'L340-H42K-0I0I-0', timezone: 'Pacific/Auckland', population: 390000, landmark: 'Christchurch Cathedral', tags: ['garden', 'rebuilt', 'south-island'], region: 'oceania' },
      { name: 'Suva', lat: -18.1416, lon: 178.4419, uCode: 'L340-H42L-0C0C-0', timezone: 'Pacific/Fiji', population: 88000, landmark: 'Suva Municipal Market', tags: ['capital', 'island', 'pacific'], region: 'oceania' },
      { name: 'Port Moresby', lat: -9.4438, lon: 147.1803, uCode: 'L340-H42K-0606-0', timezone: 'Pacific/Port_Moresby', population: 400000, landmark: 'Parliament House', tags: ['capital', 'tropical', 'highlands'], region: 'oceania' },
    ],
  },
  {
    region: 'southeast_asia',
    layer: 340,
    cities: [
      { name: 'Singapore', lat: 1.3521, lon: 103.8198, uCode: 'L340-H42H-0E0E-0', timezone: 'Asia/Singapore', population: 5700000, landmark: 'Marina Bay Sands', tags: ['city-state', 'financial', 'tropical'], region: 'southeast_asia' },
      { name: 'Bangkok', lat: 13.7563, lon: 100.5018, uCode: 'L340-H42H-0G0G-0', timezone: 'Asia/Bangkok', population: 10500000, landmark: 'Grand Palace', tags: ['capital', 'temples', 'street-food'], region: 'southeast_asia' },
      { name: 'Jakarta', lat: -6.2088, lon: 106.8456, uCode: 'L340-H42I-0808-0', timezone: 'Asia/Jakarta', population: 10600000, landmark: 'National Monument', tags: ['capital', 'megacity', 'island'], region: 'southeast_asia' },
      { name: 'Kuala Lumpur', lat: 3.1390, lon: 101.6869, uCode: 'L340-H42H-0E0E-0', timezone: 'Asia/Kuala_Lumpur', population: 1800000, landmark: 'Petronas Towers', tags: ['capital', 'multicultural', 'modern'], region: 'southeast_asia' },
      { name: 'Manila', lat: 14.5995, lon: 120.9842, uCode: 'L340-H42I-0G0G-0', timezone: 'Asia/Manila', population: 1800000, landmark: 'Intramuros', tags: ['capital', 'historic', 'coastal'], region: 'southeast_asia' },
      { name: 'Ho Chi Minh City', lat: 10.8231, lon: 106.6297, uCode: 'L340-H42I-0C0C-0', timezone: 'Asia/Ho_Chi_Minh', population: 9000000, landmark: 'Ben Thanh Market', tags: ['economic', 'vietnam', 'river'], region: 'southeast_asia' },
      { name: 'Hanoi', lat: 21.0278, lon: 105.8342, uCode: 'L340-H42I-0I0I-0', timezone: 'Asia/Ho_Chi_Minh', population: 8000000, landmark: 'Hoan Kiem Lake', tags: ['capital', 'historic', 'old-quarter'], region: 'southeast_asia' },
      { name: 'Yangon', lat: 16.8403, lon: 96.1734, uCode: 'L340-H42H-0I0I-0', timezone: 'Asia/Yangon', population: 5200000, landmark: 'Shwedagon Pagoda', tags: ['former-capital', 'temples', 'colonial'], region: 'southeast_asia' },
      { name: 'Phnom Penh', lat: 11.5564, lon: 104.9282, uCode: 'L340-H42I-0E0E-0', timezone: 'Asia/Phnom_Penh', population: 2100000, landmark: 'Royal Palace', tags: ['capital', 'river', 'cambodia'], region: 'southeast_asia' },
      { name: 'Vientiane', lat: 17.9757, lon: 102.6331, uCode: 'L340-H42I-0G0G-0', timezone: 'Asia/Vientiane', population: 820000, landmark: 'Pha That Luang', tags: ['capital', 'laos', 'mekong'], region: 'southeast_asia' },
    ],
  },
  {
    region: 'east_asia',
    layer: 340,
    cities: [
      { name: 'Tokyo', lat: 35.6762, lon: 139.6503, uCode: 'L340-H42J-0K0K-0', timezone: 'Asia/Tokyo', population: 13960000, landmark: 'Shibuya Crossing', tags: ['capital', 'megacity', 'technology'], region: 'east_asia' },
      { name: 'Seoul', lat: 37.5665, lon: 126.9780, uCode: 'L340-H42J-0K0K-0', timezone: 'Asia/Seoul', population: 9770000, landmark: 'Gyeongbokgung Palace', tags: ['capital', 'k-pop', 'technology'], region: 'east_asia' },
      { name: 'Beijing', lat: 39.9042, lon: 116.4074, uCode: 'L340-H42J-0M0M-0', timezone: 'Asia/Shanghai', population: 21540000, landmark: 'Forbidden City', tags: ['capital', 'historic', 'political'], region: 'east_asia' },
      { name: 'Shanghai', lat: 31.2304, lon: 121.4737, uCode: 'L340-H42J-0K0K-0', timezone: 'Asia/Shanghai', population: 24870000, landmark: 'The Bund', tags: ['financial', 'port', 'modern'], region: 'east_asia' },
      { name: 'Hong Kong', lat: 22.3193, lon: 114.1694, uCode: 'L340-H42J-0I0I-0', timezone: 'Asia/Hong_Kong', population: 7500000, landmark: 'Victoria Peak', tags: ['special-admin', 'financial', 'harbour'], region: 'east_asia' },
      { name: 'Taipei', lat: 25.0330, lon: 121.5654, uCode: 'L340-H42J-0I0I-0', timezone: 'Asia/Taipei', population: 2700000, landmark: 'Taipei 101', tags: ['capital', 'technology', 'night-markets'], region: 'east_asia' },
      { name: 'Osaka', lat: 34.6937, lon: 135.5023, uCode: 'L340-H42J-0K0K-0', timezone: 'Asia/Tokyo', population: 2750000, landmark: 'Osaka Castle', tags: ['food', 'commercial', 'historic'], region: 'east_asia' },
      { name: 'Guangzhou', lat: 23.1291, lon: 113.2644, uCode: 'L340-H42J-0I0I-0', timezone: 'Asia/Shanghai', population: 18680000, landmark: 'Canton Tower', tags: ['manufacturing', 'trade', 'cantonese'], region: 'east_asia' },
      { name: 'Shenzhen', lat: 22.5431, lon: 114.0579, uCode: 'L340-H42J-0I0I-0', timezone: 'Asia/Shanghai', population: 17560000, landmark: 'Window of the World', tags: ['technology', 'special-economic', 'modern'], region: 'east_asia' },
      { name: 'Busan', lat: 35.1796, lon: 129.0756, uCode: 'L340-H42J-0K0K-0', timezone: 'Asia/Seoul', population: 3400000, landmark: 'Haeundae Beach', tags: ['port', 'beach', 'festival'], region: 'east_asia' },
    ],
  },
  {
    region: 'south_asia',
    layer: 340,
    cities: [
      { name: 'Mumbai', lat: 19.0760, lon: 72.8777, uCode: 'L340-H42G-0M0M-0', timezone: 'Asia/Kolkata', population: 12480000, landmark: 'Gateway of India', tags: ['financial', 'bollywood', 'coastal'], region: 'south_asia' },
      { name: 'Delhi', lat: 28.7041, lon: 77.1025, uCode: 'L340-H42H-0O0O-0', timezone: 'Asia/Kolkata', population: 19000000, landmark: 'Red Fort', tags: ['capital', 'historic', 'political'], region: 'south_asia' },
      { name: 'Bangalore', lat: 12.9716, lon: 77.5946, uCode: 'L340-H42H-0M0M-0', timezone: 'Asia/Kolkata', population: 8440000, landmark: 'Lalbagh Botanical Garden', tags: ['technology', 'startup', 'garden-city'], region: 'south_asia' },
      { name: 'Chennai', lat: 13.0827, lon: 80.2707, uCode: 'L340-H42H-0M0M-0', timezone: 'Asia/Kolkata', population: 7090000, landmark: 'Marina Beach', tags: ['coastal', 'automotive', 'cultural'], region: 'south_asia' },
      { name: 'Kolkata', lat: 22.5726, lon: 88.3639, uCode: 'L340-H42H-0O0O-0', timezone: 'Asia/Kolkata', population: 4490000, landmark: 'Victoria Memorial', tags: ['cultural', 'historic', 'intellectual'], region: 'south_asia' },
      { name: 'Hyderabad', lat: 17.3850, lon: 78.4867, uCode: 'L340-H42H-0M0M-0', timezone: 'Asia/Kolkata', population: 6800000, landmark: 'Charminar', tags: ['technology', 'historic', 'pearls'], region: 'south_asia' },
      { name: 'Karachi', lat: 24.8607, lon: 67.0011, uCode: 'L340-H42G-0O0O-0', timezone: 'Asia/Karachi', population: 14910000, landmark: 'Mazar-e-Quaid', tags: ['port', 'financial', 'coastal'], region: 'south_asia' },
      { name: 'Dhaka', lat: 23.8103, lon: 90.4125, uCode: 'L340-H42H-0O0O-0', timezone: 'Asia/Dhaka', population: 21000000, landmark: 'Lalbagh Fort', tags: ['capital', 'megacity', 'river'], region: 'south_asia' },
      { name: 'Colombo', lat: 6.9271, lon: 79.8612, uCode: 'L340-H42H-0K0K-0', timezone: 'Asia/Colombo', population: 750000, landmark: 'Galle Face Green', tags: ['capital', 'port', 'colonial'], region: 'south_asia' },
      { name: 'Kathmandu', lat: 27.7172, lon: 85.3240, uCode: 'L340-H42H-0O0O-0', timezone: 'Asia/Kathmandu', population: 1000000, landmark: 'Boudhanath Stupa', tags: ['capital', 'himalayan', 'temples'], region: 'south_asia' },
    ],
  },
  {
    region: 'europe',
    layer: 340,
    cities: [
      { name: 'London', lat: 51.5074, lon: -0.1278, uCode: 'L340-H42D-0S0S-0', timezone: 'Europe/London', population: 8980000, landmark: 'Big Ben', tags: ['capital', 'financial', 'historic'], region: 'europe' },
      { name: 'Paris', lat: 48.8566, lon: 2.3522, uCode: 'L340-H42E-0Q0Q-0', timezone: 'Europe/Paris', population: 2160000, landmark: 'Eiffel Tower', tags: ['capital', 'fashion', 'culture'], region: 'europe' },
      { name: 'Berlin', lat: 52.5200, lon: 13.4050, uCode: 'L340-H42E-0S0S-0', timezone: 'Europe/Berlin', population: 3640000, landmark: 'Brandenburg Gate', tags: ['capital', 'history', 'creative'], region: 'europe' },
      { name: 'Madrid', lat: 40.4168, lon: -3.7038, uCode: 'L340-H42D-0Q0Q-0', timezone: 'Europe/Madrid', population: 3220000, landmark: 'Royal Palace', tags: ['capital', 'art', 'tapas'], region: 'europe' },
      { name: 'Rome', lat: 41.9028, lon: 12.4964, uCode: 'L340-H42E-0Q0Q-0', timezone: 'Europe/Rome', population: 2870000, landmark: 'Colosseum', tags: ['capital', 'ancient', 'vatican'], region: 'europe' },
      { name: 'Amsterdam', lat: 52.3676, lon: 4.9041, uCode: 'L340-H42E-0S0S-0', timezone: 'Europe/Amsterdam', population: 870000, landmark: 'Anne Frank House', tags: ['canals', 'cycling', 'museums'], region: 'europe' },
      { name: 'Brussels', lat: 50.8503, lon: 4.3517, uCode: 'L340-H42E-0S0S-0', timezone: 'Europe/Brussels', population: 1200000, landmark: 'Grand Place', tags: ['capital', 'eu', 'chocolate'], region: 'europe' },
      { name: 'Vienna', lat: 48.2082, lon: 16.3738, uCode: 'L340-H42E-0Q0Q-0', timezone: 'Europe/Vienna', population: 1900000, landmark: 'Schönbrunn Palace', tags: ['capital', 'music', 'imperial'], region: 'europe' },
      { name: 'Prague', lat: 50.0755, lon: 14.4378, uCode: 'L340-H42E-0S0S-0', timezone: 'Europe/Prague', population: 1300000, landmark: 'Charles Bridge', tags: ['capital', 'gothic', 'beer'], region: 'europe' },
      { name: 'Warsaw', lat: 52.2297, lon: 21.0122, uCode: 'L340-H42E-0S0S-0', timezone: 'Europe/Warsaw', population: 1790000, landmark: 'Palace of Culture', tags: ['capital', 'resilient', 'modern'], region: 'europe' },
      { name: 'Moscow', lat: 55.7558, lon: 37.6173, uCode: 'L340-H42E-0U0U-0', timezone: 'Europe/Moscow', population: 12500000, landmark: 'Red Square', tags: ['capital', 'historic', 'political'], region: 'europe' },
      { name: 'Istanbul', lat: 41.0082, lon: 28.9784, uCode: 'L340-H42E-0Q0Q-0', timezone: 'Europe/Istanbul', population: 15500000, landmark: 'Hagia Sophia', tags: ['cross-continental', 'historic', 'bazaar'], region: 'europe' },
      { name: 'Athens', lat: 37.9838, lon: 23.7275, uCode: 'L340-H42E-0Q0Q-0', timezone: 'Europe/Athens', population: 3150000, landmark: 'Parthenon', tags: ['capital', 'ancient', 'mediterranean'], region: 'europe' },
      { name: 'Lisbon', lat: 38.7223, lon: -9.1393, uCode: 'L340-H42D-0Q0Q-0', timezone: 'Europe/Lisbon', population: 505000, landmark: 'Belém Tower', tags: ['capital', 'coastal', 'fado'], region: 'europe' },
      { name: 'Stockholm', lat: 59.3293, lon: 18.0686, uCode: 'L340-H42E-0U0U-0', timezone: 'Europe/Stockholm', population: 975000, landmark: 'Gamla Stan', tags: ['capital', 'archipelago', 'design'], region: 'europe' },
    ],
  },
  {
    region: 'north_america',
    layer: 340,
    cities: [
      { name: 'New York', lat: 40.7128, lon: -74.0060, uCode: 'L340-H42C-0Q0Q-0', timezone: 'America/New_York', population: 8330000, landmark: 'Statue of Liberty', tags: ['financial', 'cultural', 'megacity'], region: 'north_america' },
      { name: 'Los Angeles', lat: 34.0522, lon: -118.2437, uCode: 'L340-H42B-0O0O-0', timezone: 'America/Los_Angeles', population: 3980000, landmark: 'Hollywood Sign', tags: ['entertainment', 'beach', 'sprawling'], region: 'north_america' },
      { name: 'Chicago', lat: 41.8781, lon: -87.6298, uCode: 'L340-H42C-0Q0Q-0', timezone: 'America/Chicago', population: 2710000, landmark: 'Willis Tower', tags: ['architecture', 'lake', 'deep-dish'], region: 'north_america' },
      { name: 'Toronto', lat: 43.6532, lon: -79.3832, uCode: 'L340-H42C-0S0S-0', timezone: 'America/Toronto', population: 2730000, landmark: 'CN Tower', tags: ['multicultural', 'financial', 'lake'], region: 'north_america' },
      { name: 'Vancouver', lat: 49.2827, lon: -123.1207, uCode: 'L340-H42B-0O0O-0', timezone: 'America/Vancouver', population: 631000, landmark: 'Stanley Park', tags: ['coastal', 'mountains', 'outdoor'], region: 'north_america' },
      { name: 'Montreal', lat: 45.5017, lon: -73.5673, uCode: 'L340-H42C-0S0S-0', timezone: 'America/Montreal', population: 1700000, landmark: 'Notre-Dame Basilica', tags: ['french-canadian', 'festival', 'historic'], region: 'north_america' },
      { name: 'San Francisco', lat: 37.7749, lon: -122.4194, uCode: 'L340-H42B-0O0O-0', timezone: 'America/Los_Angeles', population: 883000, landmark: 'Golden Gate Bridge', tags: ['technology', 'hills', 'fog'], region: 'north_america' },
      { name: 'Seattle', lat: 47.6062, lon: -122.3321, uCode: 'L340-H42B-0O0O-0', timezone: 'America/Los_Angeles', population: 753000, landmark: 'Space Needle', tags: ['technology', 'coffee', 'rain'], region: 'north_america' },
      { name: 'Mexico City', lat: 19.4326, lon: -99.1332, uCode: 'L340-H42C-0M0M-0', timezone: 'America/Mexico_City', population: 9200000, landmark: 'Zócalo', tags: ['capital', 'historic', 'high-altitude'], region: 'north_america' },
      { name: 'Guadalajara', lat: 20.6597, lon: -103.3496, uCode: 'L340-H42C-0M0M-0', timezone: 'America/Mexico_City', population: 1460000, landmark: 'Hospicio Cabañas', tags: ['tequila', 'technology', 'colonial'], region: 'north_america' },
    ],
  },
  {
    region: 'south_america',
    layer: 340,
    cities: [
      { name: 'São Paulo', lat: -23.5505, lon: -46.6333, uCode: 'L340-H42C-0I0I-0', timezone: 'America/Sao_Paulo', population: 12300000, landmark: 'Paulista Avenue', tags: ['financial', 'cultural', 'megacity'], region: 'south_america' },
      { name: 'Buenos Aires', lat: -34.6037, lon: -58.3816, uCode: 'L340-H42C-0G0G-0', timezone: 'America/Argentina/Buenos_Aires', population: 2890000, landmark: 'Obelisco', tags: ['capital', 'tango', 'european'], region: 'south_america' },
      { name: 'Rio de Janeiro', lat: -22.9068, lon: -43.1729, uCode: 'L340-H42C-0I0I-0', timezone: 'America/Sao_Paulo', population: 6740000, landmark: 'Christ the Redeemer', tags: ['beach', 'carnival', 'landmark'], region: 'south_america' },
      { name: 'Lima', lat: -12.0464, lon: -77.0428, uCode: 'L340-H42C-0G0G-0', timezone: 'America/Lima', population: 9750000, landmark: 'Plaza Mayor', tags: ['capital', 'coastal', 'gastronomy'], region: 'south_america' },
      { name: 'Bogotá', lat: 4.7110, lon: -74.0721, uCode: 'L340-H42C-0M0M-0', timezone: 'America/Bogota', population: 7180000, landmark: 'Monserrate', tags: ['capital', 'high-altitude', 'cultural'], region: 'south_america' },
      { name: 'Santiago', lat: -33.4489, lon: -70.6693, uCode: 'L340-H42C-0G0G-0', timezone: 'America/Santiago', population: 6150000, landmark: 'Cerro San Cristóbal', tags: ['capital', 'andes', 'wine'], region: 'south_america' },
      { name: 'Caracas', lat: 10.4806, lon: -66.9036, uCode: 'L340-H42C-0M0M-0', timezone: 'America/Caracas', population: 2940000, landmark: 'El Ávila', tags: ['capital', 'coastal', 'mountain'], region: 'south_america' },
      { name: 'Quito', lat: -0.1807, lon: -78.4678, uCode: 'L340-H42C-0G0G-0', timezone: 'America/Guayaquil', population: 1800000, landmark: 'Mitad del Mundo', tags: ['capital', 'equator', 'colonial'], region: 'south_america' },
    ],
  },
  {
    region: 'africa',
    layer: 340,
    cities: [
      { name: 'Cairo', lat: 30.0444, lon: 31.2357, uCode: 'L340-H42E-0O0O-0', timezone: 'Africa/Cairo', population: 9540000, landmark: 'Pyramids of Giza', tags: ['capital', 'ancient', 'nile'], region: 'africa' },
      { name: 'Lagos', lat: 6.5244, lon: 3.3792, uCode: 'L340-H42E-0M0M-0', timezone: 'Africa/Lagos', population: 15000000, landmark: 'Lekki Conservation Centre', tags: ['megacity', 'economic', 'coastal'], region: 'africa' },
      { name: 'Johannesburg', lat: -26.2041, lon: 28.0473, uCode: 'L340-H42E-0I0I-0', timezone: 'Africa/Johannesburg', population: 5630000, landmark: 'Apartheid Museum', tags: ['economic', 'gold', 'cultural'], region: 'africa' },
      { name: 'Nairobi', lat: -1.2921, lon: 36.8219, uCode: 'L340-H42E-0K0K-0', timezone: 'Africa/Nairobi', population: 4390000, landmark: 'Nairobi National Park', tags: ['capital', 'safari', 'technology'], region: 'africa' },
      { name: 'Casablanca', lat: 33.5731, lon: -7.5898, uCode: 'L340-H42D-0O0O-0', timezone: 'Africa/Casablanca', population: 3360000, landmark: 'Hassan II Mosque', tags: ['coastal', 'economic', 'morocco'], region: 'africa' },
      { name: 'Accra', lat: 5.6037, lon: -0.1870, uCode: 'L340-H42D-0M0M-0', timezone: 'Africa/Accra', population: 2270000, landmark: 'Kwame Nkrumah Mausoleum', tags: ['capital', 'coastal', 'ghana'], region: 'africa' },
      { name: 'Addis Ababa', lat: 9.0320, lon: 38.7469, uCode: 'L340-H42E-0K0K-0', timezone: 'Africa/Addis_Ababa', population: 3380000, landmark: 'National Palace', tags: ['capital', 'highland', 'african-union'], region: 'africa' },
      { name: 'Dakar', lat: 14.7167, lon: -17.4677, uCode: 'L340-H42D-0M0M-0', timezone: 'Africa/Dakar', population: 1140000, landmark: 'African Renaissance Monument', tags: ['capital', 'coastal', 'senegal'], region: 'africa' },
    ],
  },
  {
    region: 'middle_east',
    layer: 340,
    cities: [
      { name: 'Dubai', lat: 25.2048, lon: 55.2708, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Dubai', population: 3330000, landmark: 'Burj Khalifa', tags: ['luxury', 'financial', 'modern'], region: 'middle_east' },
      { name: 'Riyadh', lat: 24.7136, lon: 46.6753, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Riyadh', population: 7660000, landmark: 'Kingdom Centre Tower', tags: ['capital', 'oil', 'desert'], region: 'middle_east' },
      { name: 'Tel Aviv', lat: 32.0853, lon: 34.7818, uCode: 'L340-H42E-0O0O-0', timezone: 'Asia/Jerusalem', population: 4600000, landmark: 'Jaffa Old City', tags: ['technology', 'beach', 'startup'], region: 'middle_east' },
      { name: 'Tehran', lat: 35.6892, lon: 51.3890, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Tehran', population: 8690000, landmark: 'Azadi Tower', tags: ['capital', 'historic', 'mountain'], region: 'middle_east' },
      { name: 'Baghdad', lat: 33.3152, lon: 44.3661, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Baghdad', population: 6760000, landmark: 'Al-Mustansiriya University', tags: ['capital', 'historic', 'river'], region: 'middle_east' },
      { name: 'Doha', lat: 25.2854, lon: 51.5310, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Qatar', population: 1400000, landmark: 'Museum of Islamic Art', tags: ['capital', 'modern', 'gulf'], region: 'middle_east' },
      { name: 'Kuwait City', lat: 29.3759, lon: 47.9774, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Kuwait', population: 3000000, landmark: 'Kuwait Towers', tags: ['capital', 'gulf', 'oil'], region: 'middle_east' },
      { name: 'Muscat', lat: 23.5880, lon: 58.3829, uCode: 'L340-H42F-0O0O-0', timezone: 'Asia/Muscat', population: 1400000, landmark: 'Sultan Qaboos Grand Mosque', tags: ['capital', 'coastal', 'historic'], region: 'middle_east' },
    ],
  },
]

// ─── CityRegistry Singleton ───────────────────────────────────────────

class CityRegistry {
  private cities: CityMarker[] = []
  private cityMap: Map<string, CityMarker> = new Map()
  private uCodeMap: Map<string, CityMarker> = new Map()
  private regionMap: Map<string, CityMarker[]> = new Map()
  private nextTeletextPage = 300

  constructor() {
    this.loadBuiltin()
  }

  private loadBuiltin(): void {
    for (const region of BUILTIN_CITIES) {
      const regionCities: CityMarker[] = []
      for (const city of region.cities) {
        const marker: CityMarker = {
          ...city,
          teletextPage: this.nextTeletextPage++,
        }
        this.cities.push(marker)
        this.cityMap.set(marker.name.toLowerCase(), marker)
        this.uCodeMap.set(marker.uCode, marker)
        regionCities.push(marker)
      }
      this.regionMap.set(region.region, regionCities)
    }
  }

  /** Get all cities */
  getAll(): CityMarker[] {
    return this.cities
  }

  /** Find a city by name (case-insensitive, partial match) */
  findByName(name: string): CityMarker | undefined {
    const lower = name.toLowerCase()
    // Exact match first
    const exact = this.cityMap.get(lower)
    if (exact) return exact
    // Partial match
    return this.cities.find(c => c.name.toLowerCase().includes(lower))
  }

  /** Find a city by uCode */
  findByUCode(uCode: string): CityMarker | undefined {
    return this.uCodeMap.get(uCode)
  }

  /** Get all cities in a region */
  getByRegion(region: string): CityMarker[] {
    return this.regionMap.get(region) || []
  }

  /** Get all region names */
  getRegions(): string[] {
    return Array.from(this.regionMap.keys())
  }

  /** Find the nearest city to a uCode coordinate */
  findNearest(uCode: string): CityMarker | null {
    let nearest: CityMarker | null = null
    let nearestDist = Infinity
    for (const city of this.cities) {
      const dist = distanceBetween(uCode, city.uCode)
      if (dist !== null && dist < nearestDist) {
        nearestDist = dist
        nearest = city
      }
    }
    return nearest
  }

  /** Get the teletext page number for a city */
  getTeletextPage(cityName: string): number | undefined {
    const city = this.findByName(cityName)
    return city?.teletextPage
  }

  /** Get total city count */
  get count(): number {
    return this.cities.length
  }
}

// ─── Singleton export ─────────────────────────────────────────────────
export const cityRegistry = new CityRegistry()
export default cityRegistry
