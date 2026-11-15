const { app, BrowserWindow, protocol, net, ipcMain, dialog, shell, session } = require('electron')
const path = require('node:path')
const fs = require('node:fs/promises')
const { pathToFileURL } = require('node:url')
const crypto = require('node:crypto')
const zlib = require('node:zlib')
const { validateFile } = require('./validation.cjs')
const { validateProvenance } = require('./provenance.cjs')
const cloud = require('./cloud.cjs')

protocol.registerSchemesAsPrivileged([{ scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true } }])
const CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-src 'none'; form-action 'none'"
let win
let quitting = false
app.on('before-quit', () => { quitting = true })
function caller(event) {
  const url = new URL(event.senderFrame.url)
  if (event.sender !== win?.webContents || event.senderFrame !== win.webContents.mainFrame || url.protocol !== 'app:' || url.host !== 'bundle') throw new Error('Unauthorized caller')
}

app.whenReady().then(async () => {
  const root = path.join(app.getAppPath(), 'dist')
  protocol.handle('app', async request => {
    const url = new URL(request.url)
    if (url.host !== 'bundle' || request.method !== 'GET') return new Response('Not found', { status: 404 })
    const target = path.resolve(root, '.' + decodeURIComponent(url.pathname))
    if (!target.startsWith(root + path.sep)) return new Response('Not found', { status: 404 })
    try {
      const response = await net.fetch(pathToFileURL(target).href)
      const headers = new Headers(response.headers)
      headers.set('Content-Security-Policy', CSP)
      headers.set('X-Content-Type-Options', 'nosniff')
      return new Response(response.body, { status: response.status, headers })
    } catch { return new Response('Not found', { status: 404 }) }
  })
  session.defaultSession.setPermissionRequestHandler((_wc, _permission, callback) => callback(false))
  session.defaultSession.setPermissionCheckHandler(() => false)
  win = new BrowserWindow({ width: 1280, height: 900, minWidth: 760, minHeight: 600,
    title: 'Institutional Signals', backgroundColor: '#111923',
    webPreferences: { preload: path.join(__dirname, 'preload.cjs'), sandbox: true, contextIsolation: true, nodeIntegration: false, webviewTag: false } })
  win.webContents.on('will-navigate', (event, url) => { if (!url.startsWith('app://bundle/')) event.preventDefault() })
  win.webContents.on('will-attach-webview', event => event.preventDefault())
  win.on('close', event => { if (process.platform === 'darwin' && !quitting) { event.preventDefault(); win.hide() } })
  win.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const target = new URL(url)
      if (target.protocol === 'https:' && !target.username && !target.password) {
        dialog.showMessageBox(win, { type: 'question', message: 'Open publisher in your browser?', detail: target.hostname, buttons: ['Cancel', 'Open'], defaultId: 0 }).then(result => { if (result.response === 1) shell.openExternal(target.href) })
      }
    } catch {}
    return { action: 'deny' }
  })
  ipcMain.handle('app:version', event => { caller(event); return app.getVersion() })
  ipcMain.handle('workspace:connect', (event, value) => { caller(event); return cloud.connect(value) })
  ipcMain.handle('workspace:info', event => { caller(event); return cloud.info() })
  ipcMain.handle('workspace:disconnect', event => { caller(event); return cloud.disconnect() })
  ipcMain.handle('workspace:status', event => { caller(event); return cloud.call('/v1/status') })
  ipcMain.handle('evidence:list', event => { caller(event); return cloud.listLocal() })
  ipcMain.handle('evidence:submit', (event, id) => { caller(event); return cloud.submit(id) })
  ipcMain.handle('evidence:remote', event => { caller(event); return cloud.call('/v1/submissions') })
  ipcMain.handle('evidence:details', (event, id, owner) => {
    caller(event)
    if (!/^[a-f0-9-]{36}$/.test(id) || !/^[a-zA-Z0-9_-]{1,64}$/.test(owner)) throw new Error('Invalid submission')
    return cloud.call('/v1/submissions/' + id + '?owner=' + owner)
  })
  ipcMain.handle('evidence:review', (event, id, review) => {
    caller(event)
    if (!/^[a-f0-9-]{36}$/.test(id)) throw new Error('Invalid submission')
    return cloud.call('/v1/submissions/' + id + '/review', { method: 'POST', body: JSON.stringify(review), headers: { 'Content-Type': 'application/json' } })
  })
  ipcMain.handle('evidence:import', async (event, requestId, input) => {
    caller(event)
    const metadata = validateProvenance(input)
    const data = JSON.parse(await fs.readFile(path.join(root, 'data/dashboard.json'), 'utf8'))
    const request = data.upload_requests.find(r => r.request_id === requestId)
    if (!request) throw new Error('Unknown evidence request')
    const picked = await dialog.showOpenDialog(win, { title: request.document, properties: ['openFile'], filters: [{ name: 'Requested evidence', extensions: request.accepted_formats }] })
    if (picked.canceled) return { canceled: true }
    const selected = picked.filePaths[0]
    const handle = await fs.open(selected, 'r')
    let body
    try {
      if (!(await handle.stat()).isFile()) throw new Error('Select a regular file')
      const buffer = Buffer.alloc(10 * 1024 * 1024 + 1)
      const { bytesRead } = await handle.read(buffer, 0, buffer.length, 0)
      body = buffer.subarray(0, bytesRead)
    } finally { await handle.close() }
    validateFile(path.basename(selected), body, request.accepted_formats)
    const id = crypto.randomUUID()
    const hash = crypto.createHash('sha256').update(body).digest('hex')
    const folder = path.join(app.getPath('userData'), 'quarantine', id)
    await fs.mkdir(folder, { recursive: true, mode: 0o700 })
    await fs.writeFile(path.join(folder, hash + '.gz'), zlib.gzipSync(body), { flag: 'wx', mode: 0o600 })
    const record = { id, request_id: requestId, ...metadata, filename: path.basename(selected), sha256: hash, bytes: body.length, received_at: new Date().toISOString(), state: 'quarantined', scan_state: 'not_scanned', location: 'this_device_only' }
    await fs.writeFile(path.join(folder, 'manifest.json'), JSON.stringify(record), { flag: 'wx', mode: 0o600 })
    return { id, state: record.state, location: record.location }
  })
  await win.loadURL('app://bundle/index.html')
  if (app.commandLine.hasSwitch('smoke-test')) {
    try {
      const ready = await win.webContents.executeJavaScript("window.institutionalDesktop.version().then(version => ({version, title: document.title, text: document.body.innerText}))")
      if (!ready.version || !ready.title.includes('Institutional Signals')) throw new Error('Desktop preload or document failed')
      // Wait for the bundled JSON to finish loading, with a bounded deadline.
      for (let i = 0; i < 50; i++) {
        const text = await win.webContents.executeJavaScript('document.body.innerText')
        if (text.includes('What we still need')) { console.log('DESKTOP_SMOKE_OK'); app.exit(0); return }
        if (text.includes('Could not load')) throw new Error('Bundled dataset failed to load')
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      throw new Error('Dataset load timed out')
    } catch (error) { console.error(error.message); app.exit(1) }
  }
  app.on('activate', () => win?.show())
})
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
