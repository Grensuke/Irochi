/**
 * LanguageSwitcher — Multi-language dropdown selector with instant search.
 * 
 * Placed next to the light/dark mode theme toggle in both public and app layouts.
 * Features:
 * - 32 languages in strict alphabetical order (All 22 Indian scheduled languages + 10 Global languages)
 * - Real-time search filter by English name or native script
 * - Quick category filters: "All (32)", "Indian (22)", "Global (10)"
 * - Preserves strict alphabetical order across all views
 * - RTL automatic support for Arabic, Kashmiri, Sindhi, and Urdu
 * - Persists chosen language in localStorage via react-i18next
 */

import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES } from '../i18n';
import type { LanguageCode, LanguageItem } from '../i18n';
import './LanguageSwitcher.css';

interface LanguageSwitcherProps {
  /** Compact mode shows only the globe icon */
  compact?: boolean;
  className?: string;
}

type FilterTab = 'all' | 'indian' | 'global';

export function LanguageSwitcher({ compact = false, className = '' }: LanguageSwitcherProps) {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const currentLang = SUPPORTED_LANGUAGES.find(l => l.code === i18n.language)
    || SUPPORTED_LANGUAGES.find(l => l.code === 'en')
    || SUPPORTED_LANGUAGES[0];

  const handleSelect = useCallback((code: LanguageCode) => {
    i18n.changeLanguage(code);
    setOpen(false);
    setSearchQuery('');
  }, [i18n]);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (open) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    } else {
      setSearchQuery('');
    }
  }, [open]);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleClick);
    }
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    if (open) {
      document.addEventListener('keydown', handleKey);
    }
    return () => document.removeEventListener('keydown', handleKey);
  }, [open]);

  // Filter languages in strict alphabetical order
  const filteredLanguages = useMemo((): LanguageItem[] => {
    let list: readonly LanguageItem[] = SUPPORTED_LANGUAGES;

    // Apply category tab
    if (activeTab === 'indian') {
      list = list.filter(l => l.isIndian);
    } else if (activeTab === 'global') {
      list = list.filter(l => !l.isIndian);
    }

    // Apply text search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(l =>
        l.name.toLowerCase().includes(q) ||
        l.nativeName.toLowerCase().includes(q) ||
        l.code.toLowerCase().includes(q)
      );
    }

    // Always ensure alphabetical sort by English name
    return [...list].sort((a, b) => a.name.localeCompare(b.name));
  }, [activeTab, searchQuery]);

  return (
    <div ref={containerRef} className={`lang-switcher ${className}`}>
      <button
        className="lang-switcher-btn"
        onClick={() => setOpen(!open)}
        aria-label="Select language"
        aria-expanded={open}
        title={`Language: ${currentLang.name} (${currentLang.nativeName})`}
      >
        {/* Globe Icon */}
        <svg className="lang-globe-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
        {!compact && (
          <span className="lang-switcher-label">{currentLang.nativeName}</span>
        )}
        <svg className={`lang-switcher-chevron ${open ? 'open' : ''}`} width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && (
        <div className="lang-dropdown" role="listbox" aria-label="Available languages">
          <div className="lang-dropdown-header">
            <div className="lang-dropdown-title-row">
              <span className="lang-dropdown-title">{t('common.language', 'Language')}</span>
              <span className="lang-dropdown-count">32 languages</span>
            </div>

            {/* Instant Search Bar */}
            <div className="lang-search-box">
              <svg className="lang-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                ref={searchInputRef}
                type="text"
                className="lang-search-input"
                placeholder="Search languages / भाषा खोजें..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search languages"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="lang-search-clear"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Category Filter Tabs */}
            <div className="lang-filter-tabs">
              <button
                type="button"
                className={`lang-tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                onClick={() => setActiveTab('all')}
              >
                All (32)
              </button>
              <button
                type="button"
                className={`lang-tab-btn ${activeTab === 'indian' ? 'active' : ''}`}
                onClick={() => setActiveTab('indian')}
              >
                Indian (22)
              </button>
              <button
                type="button"
                className={`lang-tab-btn ${activeTab === 'global' ? 'active' : ''}`}
                onClick={() => setActiveTab('global')}
              >
                Global (10)
              </button>
            </div>
          </div>

          {/* Languages List (Alphabetical) */}
          <div className="lang-dropdown-list">
            {filteredLanguages.length === 0 ? (
              <div className="lang-dropdown-empty">
                <span>No languages found for "{searchQuery}"</span>
              </div>
            ) : (
              filteredLanguages.map((lang) => (
                <button
                  key={lang.code}
                  role="option"
                  aria-selected={lang.code === currentLang.code}
                  className={`lang-option ${lang.code === currentLang.code ? 'active' : ''}`}
                  onClick={() => handleSelect(lang.code as LanguageCode)}
                >
                  <span className="lang-option-native">{lang.nativeName}</span>
                  <span className="lang-option-english">{lang.name}</span>
                  {lang.isIndian && (
                    <span className="lang-option-indic-badge" title="Official Language of India">IN</span>
                  )}
                  {lang.code === currentLang.code && (
                    <svg className="lang-option-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
