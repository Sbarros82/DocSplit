/** Conversão simples de Markdown para HTML seguro (blog DocSplit). */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function inlineFormat(text: string): string {
  let out = escapeHtml(text)
  out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="underline underline-offset-2">$1</a>')
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  out = out.replace(/`([^`]+)`/g, '<code class="rounded bg-[#f4f5f7] px-1 py-0.5 text-[0.9em]">$1</code>')
  return out
}

export function markdownToHtml(md: string): string {
  const lines = md.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let inList = false

  const closeList = () => {
    if (inList) {
      html.push('</ul>')
      inList = false
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line.trim()) {
      closeList()
      continue
    }
    if (line.startsWith('### ')) {
      closeList()
      html.push(`<h3 class="mt-8 text-xl font-semibold tracking-tight">${inlineFormat(line.slice(4))}</h3>`)
      continue
    }
    if (line.startsWith('## ')) {
      closeList()
      html.push(`<h2 class="mt-10 text-2xl font-semibold tracking-tight">${inlineFormat(line.slice(3))}</h2>`)
      continue
    }
    if (line.startsWith('# ')) {
      closeList()
      html.push(`<h1 class="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">${inlineFormat(line.slice(2))}</h1>`)
      continue
    }
    if (line.startsWith('- ') || line.startsWith('* ')) {
      if (!inList) {
        html.push('<ul class="mt-4 list-disc space-y-2 pl-5 text-[#3a3a3a]">')
        inList = true
      }
      html.push(`<li>${inlineFormat(line.slice(2))}</li>`)
      continue
    }
    if (/^\d+\.\s/.test(line)) {
      closeList()
      const text = line.replace(/^\d+\.\s/, '')
      html.push(`<p class="mt-3 text-[15px] leading-7 text-[#3a3a3a]"><span class="font-semibold">${inlineFormat(text)}</span></p>`)
      continue
    }
    closeList()
    html.push(`<p class="mt-4 text-[15px] leading-7 text-[#3a3a3a]">${inlineFormat(line)}</p>`)
  }
  closeList()
  return html.join('\n')
}
