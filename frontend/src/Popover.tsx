import { useEffect, useId, useLayoutEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { menuPosition } from './menu-position';

export function Popover({ label, trigger, children }: { label: string; trigger: ReactNode; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null), content = useRef<HTMLDivElement>(null);
  const id = useId();
  const close = () => { setOpen(false); button.current?.focus({ preventScroll: true }); };
  useLayoutEffect(() => {
    if (!open || !content.current || !button.current) return;
    const position = () => {
      if (!content.current || !button.current) return;
      const anchor = button.current.getBoundingClientRect();
      if (anchor.bottom <= 0 || anchor.top >= innerHeight || anchor.right <= 0 || anchor.left >= document.documentElement.clientWidth) { setOpen(false); return; }
      const rect = content.current.getBoundingClientRect();
      const result = menuPosition(anchor, { width: rect.width, height: Math.min(320, content.current.scrollHeight + 2) }, { width: document.documentElement.clientWidth, height: innerHeight });
      content.current.style.setProperty('--menu-x', `${result.left}px`);
      content.current.style.setProperty('--menu-y', `${result.top}px`);
      content.current.style.setProperty('--menu-max-height', `${result.maxHeight}px`);
    };
    position(); content.current.querySelector<HTMLElement>('input,button')?.focus({ preventScroll: true });
    const observer = new ResizeObserver(position); observer.observe(content.current); observer.observe(button.current);
    addEventListener('resize', position); document.addEventListener('scroll', position, true);
    return () => { observer.disconnect(); removeEventListener('resize', position); document.removeEventListener('scroll', position, true); };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const outside = (event: PointerEvent) => { if (!button.current?.contains(event.target as Node) && !content.current?.contains(event.target as Node)) setOpen(false); };
    const keydown = (event: globalThis.KeyboardEvent) => { if (event.key === 'Escape') { event.preventDefault(); close(); } };
    document.addEventListener('pointerdown', outside); document.addEventListener('keydown', keydown);
    return () => { document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', keydown); };
  }, [open]);
  const keydown = (event: KeyboardEvent) => {
    if (event.key !== 'Tab') return;
    const items = Array.from(content.current?.querySelectorAll<HTMLElement>('input,button:not(:disabled)') ?? []);
    const index = items.indexOf(document.activeElement as HTMLElement);
    if (event.shiftKey && index === 0) { event.preventDefault(); close(); }
    else if (!event.shiftKey && index === items.length - 1) close();
  };
  return <>
    <button ref={button} type="button" className="volume-trigger" aria-label={label} aria-expanded={open} aria-controls={open ? id : undefined} onClick={() => setOpen(value => !value)} onKeyDown={event => { if (event.key === 'ArrowDown') { event.preventDefault(); setOpen(true); } }}>{trigger}</button>
    {open && createPortal(<div ref={content} id={id} role="group" aria-label={label} className="menu-content volume-popover" onKeyDown={keydown}>{children}</div>, document.body)}
  </>;
}
