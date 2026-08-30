// Paste-safe exporter. Reads live in-memory state; no page reload needed.
// Board: exactly 45" tall, aspect from VIEW_W/VIEW_H.
// Pages: 8.5 x 11 (US Letter). Edge pages are cropped — assembled board = exactly 45" tall.
window.exportPDFWithBubbles = async function() {
  const PAGE_W_IN = 8.5, PAGE_H_IN = 11;
  if (!(window.jspdf && window.jspdf.jsPDF)) return console.error('jsPDF not loaded');
  const { jsPDF } = window.jspdf;

  try { await document.fonts.ready; } catch(e) {}

  const BOARD_H_IN  = 45;
  const boardAspect = VIEW_W / VIEW_H;
  const BOARD_W_IN  = BOARD_H_IN * boardAspect;
  const DPI   = 200;
  const fullW = Math.round(BOARD_W_IN * DPI);
  const fullH = Math.round(BOARD_H_IN * DPI);
  const scale = fullH / VIEW_H; // isotropic

  console.log(`board ${BOARD_W_IN.toFixed(3)}" x ${BOARD_H_IN}" @ ${DPI} DPI = ${fullW}x${fullH}px, scale ${scale.toFixed(3)}`);

  // --- 1) Rasterize the SVG panel layer ---
  const svgStr  = new XMLSerializer().serializeToString(svg);
  const svgBlob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
  const svgUrl  = URL.createObjectURL(svgBlob);
  const svgImg  = await new Promise((res, rej) => {
    const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = svgUrl;
  });
  const board = document.createElement('canvas');
  board.width = fullW; board.height = fullH;
  const bctx = board.getContext('2d');
  bctx.fillStyle = '#fff'; bctx.fillRect(0, 0, fullW, fullH);
  bctx.drawImage(svgImg, 0, 0, fullW, fullH);
  URL.revokeObjectURL(svgUrl);

  // --- 2) Composite bubble shapes / image bubbles from live canvases ---
  for (const b of state.bubbles) {
    if (b.stackId != null) continue;
    const x = b.x * scale, y = b.y * scale;
    const w = b.w * scale, h = b.h * scale;
    if (b.type === 'image') {
      if (b.img) { try { bctx.drawImage(b.img, x, y, w, h); } catch(e){} }
    } else if (b.canvas) {
      bctx.drawImage(b.canvas, x, y, w, h);
    }
  }

  // --- 3) Composite bubble TEXT with native canvas text ---
  // Word-wrap: greedy, mirrors CSS `word-break: break-word` (chars broken if needed).
  const wrapText = (ctx, text, maxW) => {
    const outLines = [];
    for (const paragraph of (text || '').split('\n')) {
      const words = paragraph.split(/(\s+)/);
      let line = '';
      const flush = () => { outLines.push(line); line = ''; };
      const fit = (s) => ctx.measureText(s).width <= maxW;
      for (const tok of words) {
        if (!tok) continue;
        if (/^\s+$/.test(tok)) { if (line) line += ' '; continue; }
        const test = line + tok;
        if (fit(test)) { line = test; continue; }
        // doesn't fit
        if (line.trim()) flush();
        if (!fit(tok)) {
          // break the word char-by-char
          let cur = '';
          for (const ch of tok) {
            const t2 = cur + ch;
            if (!fit(t2) && cur) { outLines.push(cur); cur = ch; }
            else cur = t2;
          }
          line = cur;
        } else line = tok;
      }
      outLines.push(line);
    }
    return outLines;
  };

  for (const b of state.bubbles) {
    if (b.stackId != null) continue;
    if (b.type === 'image' || !b.text) continue;

    const ta = b.textarea;
    const cs = ta ? getComputedStyle(ta) : null;
    const style = (typeof STYLES !== 'undefined' && STYLES[b.styleKey]) || {};
    const upper = !!style.upper;

    const bx = b.x * scale, by = b.y * scale;
    const boxLeft = bx + (ta ? (parseFloat(ta.style.left) || 0) : 0) * scale;
    const boxTop  = by + (ta ? (parseFloat(ta.style.top)  || 0) : 0) * scale;
    const boxW = (ta ? (parseFloat(ta.style.width)  || b.w) : b.w) * scale;
    const boxH = (ta ? (parseFloat(ta.style.height) || b.h) : b.h) * scale;

    // .btext CSS: padding: 0 3px, box-sizing: border-box
    const padX = 3 * scale;
    const innerLeft = boxLeft + padX;
    const innerW = Math.max(1, boxW - padX * 2);

    const fontSizePx = (cs ? parseFloat(cs.fontSize) : 14) * scale;
    const family = cs ? cs.fontFamily : `"${style.font || 'sans-serif'}", cursive`;
    const weight = cs ? cs.fontWeight : 'bold';
    const italic = (cs ? cs.fontStyle : (style.italic ? 'italic' : 'normal')) === 'italic' ? 'italic ' : '';
    const color  = cs ? cs.color : '#000';

    bctx.font = `${italic}${weight} ${fontSizePx}px ${family}`;
    bctx.fillStyle = color;
    bctx.textAlign = 'center';
    bctx.textBaseline = 'top';

    const txt = upper ? b.text.toUpperCase() : b.text;
    const lines = wrapText(bctx, txt, innerW);
    const lineH = fontSizePx * 1.08; // matches .btext line-height:1.08
    // Textareas render text top-down. Small vertical breathing room from line-height gap.
    let yy = boxTop + (lineH - fontSizePx) / 2;
    const cx = innerLeft + innerW / 2;
    for (const line of lines) { bctx.fillText(line, cx, yy); yy += lineH; }
  }

  // --- 4) Tile the 45"-tall board into UNIFORM 8.5x11 pages.
  // Edge tiles get white padding so every page is 8.5x11. When assembled,
  // trim/overlap the white margins to land at exactly 45" tall.
  const tileWpx = Math.round(PAGE_W_IN * DPI);
  const tileHpx = Math.round(PAGE_H_IN * DPI);
  const cols = Math.ceil(fullW / tileWpx);
  const rows = Math.ceil(fullH / tileHpx);
  const pdf = new jsPDF({ unit: 'in', format: [PAGE_W_IN, PAGE_H_IN], orientation: 'portrait', compress: true });
  let first = true;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const srcX = c * tileWpx, srcY = r * tileHpx;
      const cropW = Math.min(tileWpx, fullW - srcX);
      const cropH = Math.min(tileHpx, fullH - srcY);
      // Uniform full-page canvas: 8.5 x 11
      const tile = document.createElement('canvas');
      tile.width = tileWpx; tile.height = tileHpx;
      const tctx = tile.getContext('2d');
      tctx.fillStyle = '#fff';
      tctx.fillRect(0, 0, tileWpx, tileHpx);
      // Draw the slice of the board into the top-left of the page tile.
      tctx.drawImage(board, srcX, srcY, cropW, cropH, 0, 0, cropW, cropH);
      const dataURL = tile.toDataURL('image/png');
      if (!first) pdf.addPage([PAGE_W_IN, PAGE_H_IN], 'portrait');
      first = false;
      pdf.addImage(dataURL, 'PNG', 0, 0, PAGE_W_IN, PAGE_H_IN);
    }
  }
  pdf.save(`roommate-billboard-letter-45in.pdf`);
  console.log(`saved: ${cols}x${rows} uniform 8.5x11 pages | board ${BOARD_W_IN.toFixed(3)}" x ${BOARD_H_IN}"`);
};
console.log('exportPDFWithBubbles ready — run: exportPDFWithBubbles()');
