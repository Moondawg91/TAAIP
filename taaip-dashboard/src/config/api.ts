/**
 * API Configuration
 * 
 * This handles API URLs for different environments:
 * - Development: uses localhost:3000 (gateway)
 * - Production: uses the gateway on the same origin (port 3000)
 * - Can be overridden with VITE_API_URL environment variable
 */

// Check if we're running in browser and what the current origin is
const getBrowserOrigin = (): string => {
  if (typeof window !== 'undefined') {
    // If on droplet or production, use the gateway port
    const { hostname, protocol } = window.location;
    
    // If hostname is not localhost, use same origin (no explicit port)
    // The gateway is proxied by Caddy at the same host/port in production.
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `${protocol}//${hostname}`;
    }
  }
  // During local frontend dev (Vite) prefer the backend on port 8000 so
  // the UI talks directly to the local backend if the gateway isn't running.
  // Vite typically serves on port 5173; detect that and target backend:8000.
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return 'http://127.0.0.1:8000';
  }
  return 'http://localhost:3000';
};

// Get API base URL
export const API_BASE = import.meta.env.VITE_API_URL || getBrowserOrigin();

console.log('API_BASE configured as:', API_BASE);
