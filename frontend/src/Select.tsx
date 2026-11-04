import { useEffect, useId, useLayoutEffect, useRef, useState, type KeyboardEvent } from 'react';
import { createPortal } from 'react-dom';
import { CaretDown, Check } from '@phosphor-icons/react';
import { menuPosition } from './menu-position';
import { filterSelectOptions } from './select-search';

export interface SelectOption { value: string; label: string; description?: string }
export function Select({ id, label, value, options, onChange, disabled = false, className = '', search }: {
  id?: string; label: string; value: string; options: SelectOption[]; onChange: (value: string) => void; disabled?: boolean; className?: string;
  search?: { label: string; empty: string };
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const trigger = useRef<HTMLButtonElement>(null), popup = useRef<HTMLDivElement>(null);
  const searchInput = useRef<HTMLInputElement>(null), results = useRef<HTMLDivElement>(null);
  const popupId = useId();
  const typeahead = useRef({ text: '', time: 0 });
  const current = options.find(option => option.value === value);
  const visible = search ? filterSelectOptions(options, query) : options;
  const show = () => { setQuery(''); setOpen(true); };
  const close = () => { setOpen(false); trigger.current?.focus({ preventScroll: true }); };
  const choose = (option: SelectOption) => { onChange(option.value); close(); };
  useLayoutEffect(() => {
    if (!open || !trigger.current || !popup.current) return;
    typeahead.current = { text: '', time: 0 };
    const position = () => {
      const anchor = trigger.current, content = popup.current; if (!anchor || !content) return;
      const rect = anchor.getBoundingClientRect();
      content.style.setProperty('--select-width', `${Math.max(200, rect.width)}px`);
      const contentRect = content.getBoundingClientRect();
      const location = menuPosition(rect, { width: contentRect.width, height: Math.min(320, content.scrollHeight + 2) }, { width: document.documentElement.clientWidth, height: innerHeight });
      content.style.setProperty('--menu-max-height', `${location.maxHeight}px`);
      content.style.setProperty('--menu-x', `${location.left}px`); content.style.setProperty('--menu-y', `${location.top}px`);
    };
    position();
    const selected = popup.current.querySelector<HTMLElement>('[aria-selected="true"]') ?? popup.current.querySelector<HTMLElement>('[role="option"]');
    (search ? searchInput.current : selected)?.focus({ preventScroll: true });
    const scroll = results.current ?? popup.current;
    if (selected) scroll.scrollTop += selected.getBoundingClientRect().top - scroll.getBoundingClientRect().top - Math.max(0, (scroll.clientHeight - selected.offsetHeight) / 2);
    const observer = new ResizeObserver(position); observer.observe(trigger.current); observer.observe(popup.current);
    addEventListener('resize', position); document.addEventListener('scroll', position, true);
    return () => { observer.disconnect(); removeEventListener('resize', position); document.removeEventListener('scroll', position, true); };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => { if (!trigger.current?.contains(event.target as Node) && !popup.current?.contains(event.target as Node)) setOpen(false); };
    const escape = (event: globalThis.KeyboardEvent) => { if (event.key === 'Escape') { event.preventDefault(); close(); } };
    document.addEventListener('pointerdown', outside); document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', escape); };
  }, [open]);
  useEffect(() => { if (disabled) setOpen(false); }, [disabled]);
  const keydown = (event: KeyboardEvent) => {
    if (event.key === 'Tab') { close(); return; }
    const items = Array.from(popup.current?.querySelectorAll<HTMLButtonElement>('[role="option"]') ?? []);
    if (event.target === searchInput.current) {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); (event.key === 'ArrowDown' ? items[0] : items.at(-1))?.focus();
      } else if (event.key === 'Enter') {
        event.preventDefault(); const option = query.trim() ? visible[0] : current; if (option) choose(option);
      }
      return;
    }
    const index = items.indexOf(document.activeElement as HTMLButtonElement);
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowUp' ? -1 : 1) + items.length) % items.length;
      items[next]?.focus();
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && event.key !== ' ') {
      event.preventDefault();
      const now = Date.now(); typeahead.current = { text: (now - typeahead.current.time < 700 ? typeahead.current.text : '') + event.key.toLocaleLowerCase(), time: now };
      if (search) { setQuery(event.key); searchInput.current?.focus({ preventScroll: true }); return; }
      const next = visible.findIndex(option => option.label.toLocaleLowerCase().startsWith(typeahead.current.text));
      if (next >= 0) items[next]?.focus();
    }
  };
  const choices = visible.map(option => <button key={option.value} type="button" role="option" aria-selected={option.value === value} tabIndex={-1} onClick={() => choose(option)}><span>{option.label}{option.description && <small>{option.description}</small>}</span>{option.value === value && <Check size={18} aria-hidden="true" />}</button>);
  return <div className={`studio-select ${className}`}>
    <button type="button" id={id} ref={trigger} role="combobox" aria-label={label} aria-haspopup="listbox" aria-controls={open ? popupId : undefined} aria-expanded={open} disabled={disabled} className="select-trigger" onClick={() => open ? close() : show()} onKeyDown={event => { if (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Home' || event.key === 'End') { event.preventDefault(); show(); } }}><span><span>{current?.label ?? value}</span>{current?.description && <small>{current.description}</small>}</span><CaretDown size={16} aria-hidden="true" /></button>
    {open && createPortal(<div ref={popup} id={search ? undefined : popupId} role={search ? undefined : 'listbox'} aria-label={search ? undefined : label} className={`menu-content select-options${search ? ' select-searchable' : ''}`} onKeyDown={keydown}>
      {search ? <><input ref={searchInput} type="search" className="select-search-field" aria-label={search.label} placeholder={search.label} aria-controls={popupId} autoComplete="off" value={query} onChange={event => { setQuery(event.target.value); if (results.current) results.current.scrollTop = 0; }} /><div ref={results} id={popupId} role="listbox" aria-label={label} className="select-search-results">{choices}</div>{!visible.length && <p className="select-search-empty" role="status">{search.empty}</p>}</> : choices}
    </div>, document.body)}
  </div>;
}
