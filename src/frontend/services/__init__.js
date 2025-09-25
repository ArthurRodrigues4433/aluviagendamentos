/**
 * Frontend services module.
 * Exports all service classes and utilities.
 */

// Core services
export { default as ApiService } from './api-service.js';
export { default as AuthService } from './auth-service.js';
export { default as SalonService } from './salon-service.js';

// UI utilities
export { default as UiUtils } from './ui-utils.js';
export { default as Formatter } from './formatter.js';

// Guards and managers
export { default as AuthGuard } from './auth-guard.js';
export { default as SalonManager } from './salon-manager.js';