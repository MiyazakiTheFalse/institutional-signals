const { contextBridge, ipcRenderer } = require('electron')
contextBridge.exposeInMainWorld('institutionalDesktop', Object.freeze({
  version: () => ipcRenderer.invoke('app:version'),
  importEvidence: requestId => typeof requestId === 'string' && requestId.length < 200
    ? ipcRenderer.invoke('evidence:import', requestId) : Promise.reject(new Error('Invalid request'))
}))
