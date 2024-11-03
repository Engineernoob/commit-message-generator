const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  generateCommitMessage: (commitType, customMessage) =>
    ipcRenderer.invoke('generate-commit-message', commitType, customMessage),
});
