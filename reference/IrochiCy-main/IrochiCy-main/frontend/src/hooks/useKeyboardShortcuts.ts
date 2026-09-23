import { useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@/hooks/useTheme';

export default function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const { toggleTheme } = useTheme();
  const gPressedRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't trigger if user is typing in an input/textarea
    const tag = (e.target as HTMLElement).tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    // "G" prefix for navigation
    if (e.key === 'g' && !e.ctrlKey && !e.metaKey) {
      if (!gPressedRef.current) {
        gPressedRef.current = true;
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => { gPressedRef.current = false; }, 800);
        return;
      }
    }

    if (gPressedRef.current) {
      gPressedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      switch (e.key) {
        case 'd': navigate('/dashboard'); e.preventDefault(); return;
        case 'a': navigate('/alerts'); e.preventDefault(); return;
        case 'n': navigate('/network'); e.preventDefault(); return;
        case 't': navigate('/threats'); e.preventDefault(); return;
      }
    }

    // "/" — focus search bar
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
      const searchInput = document.querySelector<HTMLInputElement>('.alert-filters__search-input');
      if (searchInput) { e.preventDefault(); searchInput.focus(); }
    }

    // "T" — toggle theme
    if (e.key === 't' && !e.ctrlKey && !e.metaKey && !gPressedRef.current) {
      toggleTheme();
    }

    // "?" — open keyboard shortcuts modal
    if (e.key === '?' && e.shiftKey) {
      const btn = document.querySelector<HTMLButtonElement>('#kb-shortcuts-trigger');
      if (btn) btn.click();
    }
  }, [navigate, toggleTheme]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
