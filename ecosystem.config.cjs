const path = require('path');

const root = __dirname;
const pythonBin = path.join(root, '.venv', 'bin', 'python');

module.exports = {
  apps: [
    {
      name: 'taaip-backend',
      script: pythonBin,
      args: '-m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000',
      cwd: root,
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        TAAIP_DB_PATH: process.env.TAAIP_DB_PATH || path.join(root, 'data', 'taaip.sqlite3'),
        TAAIP_UPLOAD_DIR: process.env.TAAIP_UPLOAD_DIR || path.join(root, 'services', 'api', '.data', 'imports'),
        TAAIP_REFRESH_UPLOAD_DIR: process.env.TAAIP_REFRESH_UPLOAD_DIR || path.join(root, 'data', 'refresh_uploads'),
      },
      error_file: path.join(root, 'logs', 'backend-error.log'),
      out_file: path.join(root, 'logs', 'backend-out.log'),
      log_file: path.join(root, 'logs', 'backend-combined.log'),
      time: true,
    },
    {
      name: 'taaip-frontend',
      script: 'npm',
      args: 'run dev -- --host 127.0.0.1 --port 5173',
      cwd: path.join(root, 'taaip-dashboard'),
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: path.join(root, 'logs', 'frontend-error.log'),
      out_file: path.join(root, 'logs', 'frontend-out.log'),
      log_file: path.join(root, 'logs', 'frontend-combined.log'),
      time: true,
    },
  ],
};
