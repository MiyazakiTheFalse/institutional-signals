const { contextBridge, ipcRenderer } = require('electron')
contextBridge.exposeInMainWorld('institutionalDesktop', Object.freeze({
  version: () => ipcRenderer.invoke('app:version'),
  connect: value => ipcRenderer.invoke('workspace:connect', value),
  connection: () => ipcRenderer.invoke('workspace:info'),
  disconnect: () => ipcRenderer.invoke('workspace:disconnect'),
  status: () => ipcRenderer.invoke('workspace:status'),
  localSubmissions: () => ipcRenderer.invoke('evidence:list'),
  remoteSubmissions: () => ipcRenderer.invoke('evidence:remote'),
  submissionDetails: (id, owner) => ipcRenderer.invoke('evidence:details', id, owner),
  review: (id, review) => ipcRenderer.invoke('evidence:review', id, review),
  submit: id => ipcRenderer.invoke('evidence:submit', id),
  importEvidence: (requestId, metadata) => typeof requestId === 'string' && requestId.length < 200
    ? ipcRenderer.invoke('evidence:import', requestId, metadata) : Promise.reject(new Error('Invalid request'))
}))
