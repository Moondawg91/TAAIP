export interface ZipMarketRecord {
  zip: string;
  cbsa: string;
  prizm: string;
  population: number;
  contracts: number;
  reserveVacancies: number;
  cost: number;
}

export interface EngineSummary {
  label: string;
  value: string | number;
  signal: 'good' | 'warning' | 'critical' | 'neutral';
}

export const PLACEHOLDER_MARKET_DATA: ZipMarketRecord[] = [
  { zip: '30303', cbsa: 'Atlanta', prizm: 'Urban Core', population: 12400, contracts: 92, reserveVacancies: 21, cost: 42000 },
  { zip: '30044', cbsa: 'Atlanta', prizm: 'Middle Suburb', population: 9800, contracts: 61, reserveVacancies: 38, cost: 31000 },
  { zip: '28202', cbsa: 'Charlotte', prizm: 'Young Achievers', population: 8600, contracts: 49, reserveVacancies: 33, cost: 29500 },
];
