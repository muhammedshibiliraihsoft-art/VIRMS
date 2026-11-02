export interface ThemeDefinition {
  id: string;
  name: string;
  primary: string;
  primaryHover: string;
  primaryActive: string;
  primarySoft: string;
  primarySubtle: string;
  primaryBorder: string;
  accentGradient: string;
  accentShadow: string;
  baseBg: string;
  bgGradient: string;
  cardBg: string;
  cardBorder: string;
  cardNestedBg: string;
  cardNestedBorder: string;
  sourceBaseBg?: string;
  description: string;
  isDefault?: boolean;
}

export const THEME_REGISTRY: Record<string, ThemeDefinition> = {
  orange: {
    id: 'orange',
    name: 'Orange',
    primary: '#FF551F',
    primaryHover: '#e04412',
    primaryActive: '#cc3a0a',
    primarySoft: 'rgba(255, 85, 31, 0.08)',
    primarySubtle: 'rgba(255, 85, 31, 0.035)',
    primaryBorder: 'rgba(255, 85, 31, 0.20)',
    accentGradient: 'linear-gradient(135deg, #FF4E18 0%, #FF3000 100%)',
    accentShadow: 'rgba(255, 78, 24, 0.16)',
    baseBg: '#fffdfb',
    bgGradient: `radial-gradient(circle at 28% 18%, rgba(255, 92, 45, 0.065), transparent 36%), radial-gradient(circle at 72% 42%, rgba(255, 135, 90, 0.05), transparent 42%), radial-gradient(circle at 50% 88%, rgba(255, 100, 50, 0.035), transparent 45%), linear-gradient(180deg, #fffdfb 0%, #fff9f5 100%)`,
    cardBg: '#FFFCFA',
    cardBorder: '#f0eae3',
    cardNestedBg: '#ffffff',
    cardNestedBorder: '#ede7e1',
    sourceBaseBg: '#fffdfb',
    description: 'Current baseline VIRMS palette with signature warm wash & orange highlights',
    isDefault: true,
  },
  'royal-blue': {
    id: 'royal-blue',
    name: 'Royal Blue',
    primary: '#014BAA',
    primaryHover: '#013a85',
    primaryActive: '#012c66',
    primarySoft: 'rgba(1, 75, 170, 0.08)',
    primarySubtle: 'rgba(1, 75, 170, 0.035)',
    primaryBorder: 'rgba(1, 75, 170, 0.20)',
    accentGradient: 'linear-gradient(135deg, #014BAA 0%, #003780 100%)',
    accentShadow: 'rgba(1, 75, 170, 0.18)',
    baseBg: '#fbfcfe',
    bgGradient: `radial-gradient(circle at 28% 18%, rgba(1, 75, 170, 0.05), transparent 36%), radial-gradient(circle at 72% 42%, rgba(1, 75, 170, 0.035), transparent 42%), radial-gradient(circle at 50% 88%, rgba(1, 75, 170, 0.025), transparent 45%), linear-gradient(180deg, #fbfcfe 0%, #f4f7fb 100%)`,
    cardBg: '#fafcff',
    cardBorder: '#e3ebf4',
    cardNestedBg: '#ffffff',
    cardNestedBorder: '#d9e4f0',
    sourceBaseBg: '#F8F3F0',
    description: 'Executive corporate styling with deep royal blue accents over warm light cream',
  },
  burgundy: {
    id: 'burgundy',
    name: 'Burgundy',
    primary: '#7F011F',
    primaryHover: '#630118',
    primaryActive: '#4b0011',
    primarySoft: 'rgba(127, 1, 31, 0.08)',
    primarySubtle: 'rgba(127, 1, 31, 0.035)',
    primaryBorder: 'rgba(127, 1, 31, 0.20)',
    accentGradient: 'linear-gradient(135deg, #7F011F 0%, #580015 100%)',
    accentShadow: 'rgba(127, 1, 31, 0.18)',
    baseBg: '#fffdfc',
    bgGradient: `radial-gradient(circle at 28% 18%, rgba(127, 1, 31, 0.045), transparent 36%), radial-gradient(circle at 72% 42%, rgba(127, 1, 31, 0.03), transparent 42%), radial-gradient(circle at 50% 88%, rgba(127, 1, 31, 0.02), transparent 45%), linear-gradient(180deg, #fffdfc 0%, #faf4f2 100%)`,
    cardBg: '#fffbfa',
    cardBorder: '#eee6e7',
    cardNestedBg: '#ffffff',
    cardNestedBorder: '#e7dcde',
    sourceBaseBg: '#F5EBD0',
    description: 'Rich, formal, and premium deep wine tones over warm antique parchment',
  },
  forest: {
    id: 'forest',
    name: 'Forest',
    primary: '#064734',
    primaryHover: '#043426',
    primaryActive: '#02241a',
    primarySoft: 'rgba(6, 71, 52, 0.08)',
    primarySubtle: 'rgba(6, 71, 52, 0.035)',
    primaryBorder: 'rgba(6, 71, 52, 0.20)',
    accentGradient: 'linear-gradient(135deg, #064734 0%, #032d21 100%)',
    accentShadow: 'rgba(6, 71, 52, 0.18)',
    baseBg: '#fbfefc',
    bgGradient: `radial-gradient(circle at 28% 18%, rgba(6, 71, 52, 0.045), transparent 36%), radial-gradient(circle at 72% 42%, rgba(6, 71, 52, 0.03), transparent 42%), radial-gradient(circle at 50% 88%, rgba(6, 71, 52, 0.02), transparent 45%), linear-gradient(180deg, #fbfefc 0%, #f2f8f4 100%)`,
    cardBg: '#fafffd',
    cardBorder: '#e3ebed',
    cardNestedBg: '#ffffff',
    cardNestedBorder: '#d7e5e3',
    sourceBaseBg: '#E0FFC2',
    description: 'Deep British racing green accents balanced against fresh pastel spring tones',
  },
  'midnight-indigo': {
    id: 'midnight-indigo',
    name: 'Midnight Indigo',
    primary: '#282B4A',
    primaryHover: '#1d2038',
    primaryActive: '#141628',
    primarySoft: 'rgba(40, 43, 74, 0.08)',
    primarySubtle: 'rgba(40, 43, 74, 0.035)',
    primaryBorder: 'rgba(40, 43, 74, 0.20)',
    accentGradient: 'linear-gradient(135deg, #282B4A 0%, #17192d 100%)',
    accentShadow: 'rgba(40, 43, 74, 0.18)',
    baseBg: '#fcfcfe',
    bgGradient: `radial-gradient(circle at 28% 18%, rgba(40, 43, 74, 0.045), transparent 36%), radial-gradient(circle at 72% 42%, rgba(40, 43, 74, 0.03), transparent 42%), radial-gradient(circle at 50% 88%, rgba(40, 43, 74, 0.02), transparent 45%), linear-gradient(180deg, #fcfcfe 0%, #f3f3f8 100%)`,
    cardBg: '#fbfbfe',
    cardBorder: '#e5e9ee',
    cardNestedBg: '#ffffff',
    cardNestedBorder: '#dadfe8',
    sourceBaseBg: '#EEEBDA',
    description: 'Calm, architectural, and high-contrast midnight slate over warm stone',
  },
};

export const DEFAULT_THEME_ID = 'orange';

const STORAGE_KEY = 'virms_theme_palette';

export function getStoredThemePalette(): string {
  if (typeof window === 'undefined') return DEFAULT_THEME_ID;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && THEME_REGISTRY[stored]) {
      return stored;
    }
  } catch (e) {
    // LocalStorage might be disabled or restricted
  }
  return DEFAULT_THEME_ID;
}

export function setStoredThemePalette(themeId: string): void {
  if (typeof window === 'undefined') return;
  try {
    if (THEME_REGISTRY[themeId]) {
      localStorage.setItem(STORAGE_KEY, themeId);
    } else {
      localStorage.setItem(STORAGE_KEY, DEFAULT_THEME_ID);
    }
  } catch (e) {
    // Ignore storage errors
  }
}

export function applyThemePalette(themeId: string): void {
  if (typeof document === 'undefined') return;
  const theme = THEME_REGISTRY[themeId] || THEME_REGISTRY[DEFAULT_THEME_ID];
  const root = document.documentElement;

  // Set data attribute on html for CSS variant selectors
  root.setAttribute('data-theme-palette', theme.id);

  // Set CSS custom properties on root
  root.style.setProperty('--theme-primary', theme.primary);
  root.style.setProperty('--theme-primary-hover', theme.primaryHover);
  root.style.setProperty('--theme-primary-active', theme.primaryActive);
  root.style.setProperty('--theme-primary-soft', theme.primarySoft);
  root.style.setProperty('--theme-primary-subtle', theme.primarySubtle);
  root.style.setProperty('--theme-primary-border', theme.primaryBorder);
  root.style.setProperty('--theme-accent-gradient', theme.accentGradient);
  root.style.setProperty('--theme-accent-shadow', theme.accentShadow);
  root.style.setProperty('--theme-bg-app', theme.baseBg);
  root.style.setProperty('--theme-bg-gradient', theme.bgGradient);
  root.style.setProperty('--theme-card-bg', theme.cardBg);
  root.style.setProperty('--theme-card-border', theme.cardBorder);
  root.style.setProperty('--theme-card-nested-bg', theme.cardNestedBg);
  root.style.setProperty('--theme-card-nested-border', theme.cardNestedBorder);
}
