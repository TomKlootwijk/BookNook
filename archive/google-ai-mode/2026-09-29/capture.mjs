export function capturePage() {
  const psel = '.xEFZqe [role="heading"][aria-level="2"],h2.iMqumd';
  const ps = [...document.querySelectorAll(psel)];
  const rs = [...document.querySelectorAll('.mZJni')];
  const items = [...document.querySelectorAll(psel + ',.mZJni')];
  return {
    title: document.title,
    conversationHeading: [...document.querySelectorAll('h1')].find(e => e.textContent.startsWith('AI Mode conversation'))?.textContent,
    counts: { prompts: ps.length, responses: rs.length },
    items: items.map(root => ({
      role: root.className.includes('mZJni') ? 'google' : 'user',
      text: root.innerText,
      // Keep each returned string below the browser tool's serialization limit.
      // The archive builder joins these chunks without changing the markup.
      html: root.outerHTML.length <= 90000 ? root.outerHTML : '',
      htmlChunks: root.outerHTML.length > 90000 ? root.outerHTML.match(/[\s\S]{1,90000}/g) : undefined,
      equations: [...root.querySelectorAll('[data-xpm-latex]')].map(x => x.getAttribute('data-xpm-latex')),
      links: [...root.querySelectorAll('a[href]')].map(a => ({ text: a.innerText || a.getAttribute('aria-label') || '', url: a.href })),
      images: [...root.querySelectorAll('img')].filter(i => !i.getAttribute('data-xpm-latex') && !i.src.startsWith('data:image/gif')).map(i => ({ url: i.currentSrc || i.src, alt: i.alt, width: i.naturalWidth, height: i.naturalHeight })),
      canvases: root.querySelectorAll('canvas').length
    })),
    controls: [...document.querySelectorAll('button')].map(e => e.getAttribute('aria-label') || e.innerText).filter(s => /^(load|older|earlier|show more|continue|show .*code)/i.test(s))
  };
}
