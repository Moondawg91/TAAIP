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
  return 'http://localhost:3000';
};

// Get API base URL
export const API_BASE = import.meta.env.VITE_API_URL || getBrowserOrigin();

console.log('API_BASE configured as:', API_BASE);
