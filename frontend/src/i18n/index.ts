import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Locale imports in alphabetical order by language name
import ar from './locales/ar.json';     // Arabic
import as from './locales/as.json';     // Assamese
import bn from './locales/bn.json';     // Bengali
import brx from './locales/brx.json';   // Bodo
import zh from './locales/zh.json';     // Chinese
import doi from './locales/doi.json';   // Dogri
import en from './locales/en.json';     // English
import fr from './locales/fr.json';     // French
import de from './locales/de.json';     // German
import gu from './locales/gu.json';     // Gujarati
import hi from './locales/hi.json';     // Hindi
import ja from './locales/ja.json';     // Japanese
import kn from './locales/kn.json';     // Kannada
import ks from './locales/ks.json';     // Kashmiri
import kok from './locales/kok.json';   // Konkani
import ko from './locales/ko.json';     // Korean
import mai from './locales/mai.json';   // Maithili
import ml from './locales/ml.json';     // Malayalam
import mni from './locales/mni.json';   // Manipuri
import mr from './locales/mr.json';     // Marathi
import ne from './locales/ne.json';     // Nepali
import or from './locales/or.json';     // Odia
import pt from './locales/pt.json';     // Portuguese
import pa from './locales/pa.json';     // Punjabi
import ru from './locales/ru.json';     // Russian
import sa from './locales/sa.json';     // Sanskrit
import sat from './locales/sat.json';   // Santali
import sd from './locales/sd.json';     // Sindhi
import es from './locales/es.json';     // Spanish
import ta from './locales/ta.json';     // Tamil
import te from './locales/te.json';     // Telugu
import ur from './locales/ur.json';     // Urdu

/**
 * All 32 supported languages in strict alphabetical order by English name.
 * Includes all 22 Eighth Schedule official languages of India + major international languages.
 */
export const SUPPORTED_LANGUAGES = [
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', dir: 'rtl', isIndian: false },
  { code: 'as', name: 'Assamese', nativeName: 'অসমীয়া', dir: 'ltr', isIndian: true },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', dir: 'ltr', isIndian: true },
  { code: 'brx', name: 'Bodo', nativeName: 'बड़ो', dir: 'ltr', isIndian: true },
  { code: 'zh', name: 'Chinese', nativeName: '中文', dir: 'ltr', isIndian: false },
  { code: 'doi', name: 'Dogri', nativeName: 'डोगरी', dir: 'ltr', isIndian: true },
  { code: 'en', name: 'English', nativeName: 'English', dir: 'ltr', isIndian: false },
  { code: 'fr', name: 'French', nativeName: 'Français', dir: 'ltr', isIndian: false },
  { code: 'de', name: 'German', nativeName: 'Deutsch', dir: 'ltr', isIndian: false },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', dir: 'ltr', isIndian: true },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', dir: 'ltr', isIndian: true },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', dir: 'ltr', isIndian: false },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', dir: 'ltr', isIndian: true },
  { code: 'ks', name: 'Kashmiri', nativeName: 'کٲشُر', dir: 'rtl', isIndian: true },
  { code: 'kok', name: 'Konkani', nativeName: 'कोंकणी', dir: 'ltr', isIndian: true },
  { code: 'ko', name: 'Korean', nativeName: '한국어', dir: 'ltr', isIndian: false },
  { code: 'mai', name: 'Maithili', nativeName: 'मैथिली', dir: 'ltr', isIndian: true },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', dir: 'ltr', isIndian: true },
  { code: 'mni', name: 'Manipuri', nativeName: 'মৈতৈলোন্', dir: 'ltr', isIndian: true },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी', dir: 'ltr', isIndian: true },
  { code: 'ne', name: 'Nepali', nativeName: 'नेपाली', dir: 'ltr', isIndian: true },
  { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ', dir: 'ltr', isIndian: true },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', dir: 'ltr', isIndian: false },
  { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', dir: 'ltr', isIndian: true },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', dir: 'ltr', isIndian: false },
  { code: 'sa', name: 'Sanskrit', nativeName: 'संस्कृतम्', dir: 'ltr', isIndian: true },
  { code: 'sat', name: 'Santali', nativeName: 'ᱥᱟᱱᱛᱟᱲᱤ', dir: 'ltr', isIndian: true },
  { code: 'sd', name: 'Sindhi', nativeName: 'سنڌي', dir: 'rtl', isIndian: true },
  { code: 'es', name: 'Spanish', nativeName: 'Español', dir: 'ltr', isIndian: false },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', dir: 'ltr', isIndian: true },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', dir: 'ltr', isIndian: true },
  { code: 'ur', name: 'Urdu', nativeName: 'اُردُو', dir: 'rtl', isIndian: true },
] as const;

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number]['code'];
export type LanguageItem = (typeof SUPPORTED_LANGUAGES)[number];

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      ar: { translation: ar },
      as: { translation: as },
      bn: { translation: bn },
      brx: { translation: brx },
      zh: { translation: zh },
      doi: { translation: doi },
      en: { translation: en },
      fr: { translation: fr },
      de: { translation: de },
      gu: { translation: gu },
      hi: { translation: hi },
      ja: { translation: ja },
      kn: { translation: kn },
      ks: { translation: ks },
      kok: { translation: kok },
      ko: { translation: ko },
      mai: { translation: mai },
      ml: { translation: ml },
      mni: { translation: mni },
      mr: { translation: mr },
      ne: { translation: ne },
      or: { translation: or },
      pt: { translation: pt },
      pa: { translation: pa },
      ru: { translation: ru },
      sa: { translation: sa },
      sat: { translation: sat },
      sd: { translation: sd },
      es: { translation: es },
      ta: { translation: ta },
      te: { translation: te },
      ur: { translation: ur },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already handles XSS
    },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'vibhinetra-language',
      caches: ['localStorage'],
    },
  });

// Set initial dir attribute based on detected language
const currentLang = SUPPORTED_LANGUAGES.find(l => l.code === i18n.language) 
  || SUPPORTED_LANGUAGES.find(l => l.code === 'en')
  || SUPPORTED_LANGUAGES[0];

if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('lang', currentLang.code);
  document.documentElement.setAttribute('dir', currentLang.dir);
}

// Listen for language changes and update dir/lang attributes
i18n.on('languageChanged', (lng: string) => {
  const lang = SUPPORTED_LANGUAGES.find(l => l.code === lng) || SUPPORTED_LANGUAGES[0];
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('lang', lang.code);
    document.documentElement.setAttribute('dir', lang.dir);
    localStorage.setItem('vibhinetra-language', lng);
  }
});

export default i18n;
