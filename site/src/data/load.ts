import fs from 'node:fs';
import path from 'node:path';

// Handle both: `astro build` from site/ (cwd=site, data=../data)
// and `astro dev --root site` from project root (cwd=sg-charity, data=./data)
function findDataDir(): string {
  const candidates = [
    path.resolve(process.cwd(), 'data'),
    path.resolve(process.cwd(), '../data'),
  ];
  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, 'charities_unified.json'))) {
      return dir;
    }
  }
  throw new Error(`Data directory not found. Checked: ${candidates.join(', ')}`);
}

const DATA_DIR = findDataDir();

export interface Charity {
  uen: string;
  name: string;
  slug: string;
  status: string;
  is_active: boolean;
  ipc_status: string | null;
  ipc_valid_from: string | null;
  ipc_valid_till: string | null;
  sector: string | null;
  classifications: string[];
  activities: string[];
  setup: string | null;
  administrator: string | null;
  registration_date: string | null;
  deregistration_date: string | null;
  contact_person: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  address: string | null;
  postal_code: string | null;
  objective: string | null;
  vision_mission: string | null;
  org_activities: string[];
  governing_members_count: number;
  key_officers_count: number;
  governing_members: { name: string; designation: string }[];
  key_officers: { name: string; designation: string }[];
  has_public_financials: boolean;
  financials: FinancialData | null;
  latitude: number | null;
  longitude: number | null;
  givingsg_description: string | null;
  givingsg_causes: string[];
  givingsg_image: string | null;
  givingsg_url: string | null;
}

export interface FinancialSummary {
  period: string;
  income: number | null;
  spending: number | null;
  status: string;
}

export interface FinancialData {
  summaries: FinancialSummary[];
  receipts: Record<string, Record<string, number>>;
  expenses: Record<string, Record<string, number>>;
  balance_sheet: Record<string, Record<string, number>>;
  other_info: Record<string, Record<string, number>>;
}

export interface Stats {
  total: number;
  active: number;
  deregistered: number;
  with_profile: number;
  with_financials: number;
  with_geo: number;
  with_givingsg: number;
  sectors: Record<string, number>;
  ipc_active: number;
  ipc_expiring_2026: number;
}

let _charities: Charity[] | null = null;
let _stats: Stats | null = null;

export function loadCharities(): Charity[] {
  if (!_charities) {
    const raw = fs.readFileSync(path.join(DATA_DIR, 'charities_unified.json'), 'utf-8');
    _charities = JSON.parse(raw);
  }
  return _charities!;
}

export function loadStats(): Stats {
  if (!_stats) {
    const raw = fs.readFileSync(path.join(DATA_DIR, 'charities_unified_stats.json'), 'utf-8');
    _stats = JSON.parse(raw);
  }
  return _stats!;
}

export function getActiveCharities(): Charity[] {
  return loadCharities().filter(c => c.is_active);
}

export function getCharityBySlug(slug: string): Charity | undefined {
  return loadCharities().find(c => c.slug === slug);
}

export function getCharitiesBySector(sector: string): Charity[] {
  return getActiveCharities().filter(c => c.sector === sector);
}

export function getSectors(): string[] {
  return ['Social and Welfare', 'Health', 'Education', 'Religious', 'Arts and Heritage', 'Community', 'Sports', 'Others'];
}

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '-';
  return new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD', maximumFractionDigits: 0 }).format(amount);
}

export function stripHtml(html: string | null): string {
  if (!html) return '';
  return html.replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '').trim();
}

export const SECTOR_COLORS: Record<string, string> = {
  'Social and Welfare': '#3b82f6',
  'Health': '#ef4444',
  'Education': '#f59e0b',
  'Religious': '#8b5cf6',
  'Arts and Heritage': '#ec4899',
  'Community': '#10b981',
  'Sports': '#f97316',
  'Others': '#6b7280',
};

export const SECTOR_ICONS: Record<string, string> = {
  'Social and Welfare': '🤝',
  'Health': '🏥',
  'Education': '📚',
  'Religious': '🛕',
  'Arts and Heritage': '🎨',
  'Community': '🏘️',
  'Sports': '⚽',
  'Others': '📋',
};
