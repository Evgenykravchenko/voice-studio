export interface MenuAnchor { left: number; right: number; top: number; bottom: number }

/** Keep the popup attached to its trigger; scroll tall content on the roomier side. */
export function menuPosition(anchor: MenuAnchor, menu: { width: number; height: number }, viewport: { width: number; height: number }) {
  const gutter = 8;
  const width = Math.min(menu.width, Math.max(0, viewport.width - gutter * 2));
  const below = Math.max(0, viewport.height - gutter * 2 - anchor.bottom);
  const above = Math.max(0, anchor.top - gutter * 2);
  const opensBelow = menu.height <= below || below >= above;
  const maxHeight = Math.min(320, Math.max(0, viewport.height - gutter * 2), opensBelow ? below : above);
  const height = Math.min(menu.height, maxHeight);
  const preferredTop = opensBelow ? anchor.bottom + gutter : anchor.top - gutter - height;
  return {
    left: Math.max(gutter, Math.min(anchor.right - width, viewport.width - width - gutter)),
    top: Math.max(gutter, Math.min(preferredTop, viewport.height - height - gutter)),
    maxHeight,
  };
}
