module.exports = {
  apps: [
    {
      name: 'taaip-backend',
      script: '/usr/bin/python3',
      args: '-m uvicorn taaip_service:app --host 0.0.0.0 --port 8000',
      cwd: '/Users/ambermooney/Desktop/TAAIP',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend-combined.log',
      time: true
    },
    {
      name: 'taaip-frontend',
      script: 'npm',
      args: 'run dev -- --host',
      cwd: '/Users/ambermooney/Desktop/TAAIP/taaip-dashboard',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true
    }
  ]
};
