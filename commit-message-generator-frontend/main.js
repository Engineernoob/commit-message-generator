const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,      // Ensures security by disabling Node integration in the renderer
      contextIsolation: true,      // Enables contextIsolation to use contextBridge
      enableRemoteModule: false,   // Improves security by disabling remote module in renderer
    },
  });

  mainWindow.loadFile('public/index.html');
}


app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handler for generating commit message
ipcMain.handle('generate-commit-message', async (event, commitType, customMessage) => {
  return new Promise((resolve, reject) => {
    // Spawn Python process
    const pythonProcess = spawn('python', [
      'path/to/commit_tool.py', // Update with the actual path to your Python script
      '--generate',
      `--type=${commitType}`,
      `--message=${customMessage}`
    ]);

    pythonProcess.stdout.on('data', (data) => {
      resolve(data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
  
      reject(data.toString());
    });
  });
});