import { useEffect, useLayoutEffect, useId, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { CaretDown, type Icon } from '@phosphor-icons/react';
import { menuPosition } from './menu-position';

export function Menu({ label, icon: Glyph, children, className = '' }: { label: string; icon?: Icon; children: ReactNode; className?: string }) {
  const [open, setOpen] = useState(false);
  const popupId = useId();
  const ref = useRef<HTMLDivElement>(null);
  const popup = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (!open || !popup.current) return;
    const position = () => {
      const trigger = ref.current?.querySelector('button'), content = popup.current;
      if (!trigger || !content) return;
      const rect = content.getBoundingClientRect();
      const { left, top, maxHeight } = menuPosition(trigger.getBoundingClientRect(), { width: rect.width, height: Math.min(320, content.scrollHeight + 2) }, { width: document.documentElement.clientWidth, height: innerHeight });
      content.style.setProperty('--menu-x', `${left}px`);
      content.style.setProperty('--menu-y', `${top}px`);
      content.style.setProperty('--menu-max-height', `${maxHeight}px`);
    };
    position();
    (popup.current.querySelector<HTMLElement>('[aria-pressed="true"]') ?? popup.current.querySelector<HTMLElement>('button:not(:disabled), a[href]'))?.focus({ preventScroll: true });
    const resize = new ResizeObserver(position);
    resize.observe(popup.current);
    if (ref.current) resize.observe(ref.current);
    addEventListener('resize', position);
    document.addEventListener('scroll', position, true);
    return () => { resize.disconnect(); removeEventListener('resize', position); document.removeEventListener('scroll', position, true); };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const outside = (e: PointerEvent) => { if (!ref.current?.contains(e.target as Node) && !popup.current?.contains(e.target as Node)) setOpen(false); };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'Tab') {
        if (e.key === 'Escape') e.preventDefault();
        setOpen(false); ref.current?.querySelector('button')?.focus({ preventScroll: true });
      }
      if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) {
        const items = Array.from(popup.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href]') ?? []);
        if (!items.length) return;
        e.preventDefault();
        const current = items.indexOf(document.activeElement as HTMLElement);
        const next = e.key === 'Home' ? 0 : e.key === 'End' ? items.length - 1 : (current + (e.key === 'ArrowUp' ? -1 : 1) + items.length) % items.length;
        items[next].focus();
      }
    };
    document.addEventListener('pointerdown', outside); document.addEventListener('keydown', key);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', key); };
  }, [open]);
  return <div className={`menu ${className}`} ref={ref}>
    <button type="button" className="menu-trigger" aria-controls={open ? popupId : undefined} aria-expanded={open} aria-label={label} onClick={() => setOpen(!open)}>{Glyph && <Glyph size={20} />}<span>{label}</span><CaretDown size={14} /></button>
    {open && createPortal(<div ref={popup} id={popupId} role="group" aria-label={label} className="menu-content" onClick={event => { if (!(event.target as Element).closest('button, a[href]')) return; setOpen(false); ref.current?.querySelector('button')?.focus({ preventScroll: true }); }}>{children}</div>, document.body)}
  </div>;
}

