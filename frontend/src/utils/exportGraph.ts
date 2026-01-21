/**
 * Export graph visualization as image
 */
export async function exportGraphAsImage(
  containerElement: HTMLElement | null,
  filename: string = `graph-export-${Date.now()}.png`
): Promise<void> {
  if (!containerElement) {
    throw new Error('Container element not found')
  }

  try {
    // Try using html2canvas if available
    const html2canvas = (window as any).html2canvas
    if (html2canvas) {
      const canvas = await html2canvas(containerElement, {
        backgroundColor: '#0A0F1E',
        useCORS: true,
        scale: 2, // Higher quality
      })
      
      const dataUrl = canvas.toDataURL('image/png')
      downloadImage(dataUrl, filename)
      return
    }

    // Fallback: Try to get canvas from WebGL context
    const canvas = containerElement.querySelector('canvas')
    if (canvas) {
      const dataUrl = canvas.toDataURL('image/png')
      downloadImage(dataUrl, filename)
      return
    }

    throw new Error('No canvas element found for export')
  } catch (error) {
    console.error('Failed to export graph:', error)
    throw error
  }
}

function downloadImage(dataUrl: string, filename: string): void {
  const link = document.createElement('a')
  link.download = filename
  link.href = dataUrl
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * Export graph data as JSON
 */
export function exportGraphAsJSON(
  nodes: any[],
  links: any[],
  filename: string = `graph-data-${Date.now()}.json`
): void {
  const data = {
    nodes,
    links,
    exportedAt: new Date().toISOString(),
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.download = filename
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
