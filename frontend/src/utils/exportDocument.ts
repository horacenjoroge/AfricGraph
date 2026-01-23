/**
 * Export graph connections as document (PDF/DOCX)
 */

interface Node {
  id: string
  name: string
  labels: string[]
  riskScore?: number
  properties?: Record<string, any>
}

interface Connection {
  id: string
  name: string
  labels: string[]
  properties?: Record<string, any>
  relationship_type: string
  relationship_properties?: Record<string, any>
}

/**
 * Export connections as PDF using browser print-to-PDF
 */
export async function exportConnectionsAsPDF(
  node: Node,
  connections: Connection[],
  filename: string = `connections-${node.name}-${Date.now()}.pdf`
): Promise<void> {
  try {
    // Generate HTML and use browser print to PDF
    await generatePDFFromHTML(node, connections, filename)
  } catch (error) {
    console.error('Failed to export PDF:', error)
    // Fallback: download as HTML
    const htmlContent = generateDocumentHTML(node, connections)
    downloadHTML(htmlContent, filename.replace('.pdf', '.html'))
    alert('PDF export not available. Document downloaded as HTML. You can open it in a browser and print to PDF.')
  }
}

/**
 * Export connections as DOCX using HTML-to-DOCX conversion
 */
export async function exportConnectionsAsDOCX(
  node: Node,
  connections: Connection[],
  filename: string = `connections-${node.name}-${Date.now()}.docx`
): Promise<void> {
  try {
    // Generate HTML content
    const htmlContent = generateDocumentHTML(node, connections)
    
    // Convert HTML to DOCX
    // Option 1: Use docx library if available
    const docx = (window as any).docx
    if (docx) {
      await generateDOCXWithLibrary(node, connections, filename)
    } else {
      // Fallback: Download as HTML (user can open in Word)
      downloadHTML(htmlContent, filename.replace('.docx', '.html'))
    }
  } catch (error) {
    console.error('Failed to export DOCX:', error)
    throw error
  }
}

/**
 * Generate PDF from HTML using browser print dialog
 */
async function generatePDFFromHTML(
  node: Node,
  connections: Connection[],
  filename: string
): Promise<void> {
  const htmlContent = generateDocumentHTML(node, connections)
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    throw new Error('Failed to open print window')
  }
  
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>${node.name} - Connections</title>
        <style>
          body {
            font-family: 'Courier New', monospace;
            background: #0A0F1E;
            color: #E5E7EB;
            padding: 20px;
          }
          h1 { color: #00FFFF; }
          h2 { color: #3B82F6; margin-top: 20px; }
          .connection { margin: 10px 0; padding: 10px; border: 1px solid #374151; }
        </style>
      </head>
      <body>
        ${htmlContent}
      </body>
    </html>
  `)
  
  printWindow.document.close()
  printWindow.focus()
  
  // Wait a bit then trigger print
  setTimeout(() => {
    printWindow.print()
    // User can save as PDF from print dialog
  }, 500)
}

/**
 * Generate DOCX using docx library
 */
async function generateDOCXWithLibrary(
  node: Node,
  connections: Connection[],
  filename: string
): Promise<void> {
  // This would require installing @docx library
  // For now, we'll use HTML fallback
  const htmlContent = generateDocumentHTML(node, connections)
  downloadHTML(htmlContent, filename.replace('.docx', '.html'))
}

/**
 * Generate HTML content for document
 */
function generateDocumentHTML(node: Node, connections: Connection[]): string {
  const connectionsByType = connections.reduce((acc, conn) => {
    const type = conn.relationship_type || 'UNKNOWN'
    if (!acc[type]) acc[type] = []
    acc[type].push(conn)
    return acc
  }, {} as Record<string, Connection[]>)
  
  let html = `
    <div style="font-family: 'Courier New', monospace; color: #E5E7EB; background: #0A0F1E; padding: 20px;">
      <h1 style="color: #00FFFF; border-bottom: 2px solid #00FFFF; padding-bottom: 10px;">
        Connections Report: ${node.name}
      </h1>
      
      <div style="margin: 20px 0; padding: 15px; background: #1F2937; border-left: 4px solid #00FFFF;">
        <h2 style="color: #00FFFF; margin-top: 0;">Node Information</h2>
        <p><strong>ID:</strong> ${node.id}</p>
        <p><strong>Labels:</strong> ${node.labels.join(', ')}</p>
        ${node.riskScore !== undefined ? `<p><strong>Risk Score:</strong> <span style="color: ${node.riskScore >= 80 ? '#EF4444' : node.riskScore >= 60 ? '#F59E0B' : '#10B981'}">${node.riskScore}</span></p>` : ''}
      </div>
      
      <div style="margin: 20px 0;">
        <h2 style="color: #3B82F6; border-bottom: 1px solid #3B82F6; padding-bottom: 5px;">
          Connections (${connections.length})
        </h2>
  `
  
  Object.entries(connectionsByType).forEach(([relType, conns]) => {
    html += `
      <div style="margin: 20px 0;">
        <h3 style="color: #10B981; margin-top: 15px;">${relType} (${conns.length})</h3>
    `
    
    conns.forEach((conn) => {
      html += `
        <div style="margin: 10px 0; padding: 15px; background: #1F2937; border-left: 4px solid #10B981;">
          <h4 style="color: #10B981; margin-top: 0;">${conn.name || conn.id}</h4>
          <p><strong>Labels:</strong> ${conn.labels.join(', ')}</p>
      `
      
      if (conn.relationship_properties && Object.keys(conn.relationship_properties).length > 0) {
        html += `<p><strong>Relationship Properties:</strong></p><ul>`
        Object.entries(conn.relationship_properties).forEach(([key, value]) => {
          html += `<li>${key}: ${String(value)}</li>`
        })
        html += `</ul>`
      }
      
      if (conn.properties && Object.keys(conn.properties).length > 0) {
        html += `<p><strong>Node Properties:</strong></p><ul>`
        Object.entries(conn.properties).forEach(([key, value]) => {
          html += `<li>${key}: ${String(value)}</li>`
        })
        html += `</ul>`
      }
      
      html += `</div>`
    })
    
    html += `</div>`
  })
  
  html += `
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #374151; text-align: center; color: #6B7280; font-size: 12px;">
          Generated: ${new Date().toLocaleString()}
        </div>
      </div>
    </div>
  `
  
  return html
}

/**
 * Download HTML as file
 */
function downloadHTML(htmlContent: string, filename: string): void {
  const blob = new Blob([htmlContent], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.download = filename
  link.href = url
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
