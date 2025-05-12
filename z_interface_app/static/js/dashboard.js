/**
 * AI Model Management Dashboard
 * Optimized JavaScript implementation using ES6 classes
 */

// Main Application Class
class Dashboard {
  /**
   * Initialize the dashboard application
   */
  constructor() {
    // Core services
    this.config = new ConfigurationManager();
    this.eventManager = new EventManager();
    this.errorHandler = new ErrorHandler(this);
    this.stateManager = new StateManager();
    this.apiService = new ApiService(this.config, this.errorHandler);
    this.utilityService = new UtilityService(this.errorHandler);
    this.uiService = new UIService(this);
    this.pollingService = new PollingService(this);
    
    // Controllers
    this.coreController = new CoreController(this);
    this.uiController = new UIController(this);
    
    // Feature management
    this.featureManager = new FeatureManager(this);
  }

  /**
   * Initialize the application and all components
   */
  init() {
    console.log('Initializing AI Model Management Dashboard');
    
    // Load configuration
    this.config.loadStoredSettings();
    
    // Initialize controllers
    this.coreController.init();
    this.uiController.init();
    
    // Set up global event handlers
    this.setupGlobalListeners();
    
    // Initialize feature modules
    this.featureManager.initFeatures();
    
    // Perform initial refresh
    if (this.config.autoRefresh.enabled) {
      this.coreController.refreshAllStatuses();
    }
  }

  /**
   * Set up global event handlers
   */
  setupGlobalListeners() {
    // Handle visibility change to manage auto-refresh
    this.eventManager.on(document, 'visibilitychange', () => {
      if (document.hidden) {
        this.coreController.autoRefreshService.pause();
      } else {
        this.coreController.autoRefreshService.resume();
      }
    });
    
    // Set up global error handling
    window.addEventListener('error', this.errorHandler.handleGlobalError.bind(this.errorHandler));
    
    // Handle page unload to clean up resources
    window.addEventListener('beforeunload', () => {
      // Stop all polling activities
      this.pollingService.stopAllPolling();
      // Remove all event listeners
      this.eventManager.offAll();
    });
  }
}

/**
 * Configuration Manager Class
 * Manages application settings
 */
class ConfigurationManager {
  constructor() {
    this.autoRefresh = {
      enabled: false,
      interval: 30000,
      timer: null
    };
    
    this.api = {
      retryAttempts: 3,
      retryDelay: 1000,
      timeout: 30000
    };
    
    this.ui = {
      toastDuration: 3000,
      maxLogLines: 500
    };
    
    this.animations = {
      enabled: true
    };
  }

  /**
   * Load settings from localStorage
   */
  loadStoredSettings() {
    try {
      const storedSettings = localStorage.getItem('dashboardSettings');
      if (storedSettings) {
        const settings = JSON.parse(storedSettings);
        // Use nullish coalescing to safely set values
        this.autoRefresh.enabled = settings.autoRefresh?.enabled ?? this.autoRefresh.enabled;
        this.autoRefresh.interval = settings.autoRefresh?.interval ?? this.autoRefresh.interval;
        this.animations.enabled = settings.animations?.enabled ?? this.animations.enabled;
      }
    } catch (e) {
      console.warn('Failed to load stored settings:', e);
    }
  }

  /**
   * Save settings to localStorage
   */
  saveSettings() {
    try {
      const settings = {
        autoRefresh: {
          enabled: this.autoRefresh.enabled,
          interval: this.autoRefresh.interval
        },
        animations: {
          enabled: this.animations.enabled
        }
      };
      localStorage.setItem('dashboardSettings', JSON.stringify(settings));
    } catch (e) {
      console.warn('Failed to save settings:', e);
    }
  }
}

/**
 * Event Manager Class
 * Manages event listeners with proper cleanup
 */
class EventManager {
  constructor() {
    this.handlers = new Map();
    this.idCounter = 0;
  }
  
  /**
   * Add event listener with optional delegation
   * @param {Element|Document|Window} element - Element to attach listener to
   * @param {string} eventType - Event type (e.g., 'click')
   * @param {string|Function} selector - CSS selector for delegation or handler function
   * @param {Function} [handler] - Event handler (if selector is provided)
   * @returns {string} - Handler ID for removal
   */
  on(element, eventType, selector, handler) {
    // If only 3 arguments passed, second is handler, not selector
    if (typeof selector === 'function') {
      handler = selector;
      selector = null;
    }
    
    // Create wrapped handler for proper delegation
    const wrappedHandler = selector 
      ? (e) => { 
          if ($(e.target).is(selector) || $(e.target).closest(selector).length) {
            handler.call(this, e); 
          }
        }
      : handler;
    
    // Generate unique handler ID
    const id = `handler_${++this.idCounter}`;
    
    // Store handler details
    this.handlers.set(id, { 
      element, 
      eventType, 
      wrappedHandler,
      originalHandler: handler 
    });
    
    // Attach event
    $(element).on(eventType, wrappedHandler);
    
    return id;
  }
  
  /**
   * Remove event listener by ID
   * @param {string} id - Handler ID
   * @returns {boolean} - Success status
   */
  off(id) {
    if (!this.handlers.has(id)) return false;
    
    const { element, eventType, wrappedHandler } = this.handlers.get(id);
    $(element).off(eventType, wrappedHandler);
    this.handlers.delete(id);
    
    return true;
  }
  
  /**
   * Remove all registered event listeners
   */
  offAll() {
    this.handlers.forEach((handler, id) => {
      this.off(id);
    });
  }
}

/**
 * Error Handler Class
 * Centralized error handling
 */
class ErrorHandler {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }
  
  /**
   * Handle error with logging and notification
   * @param {Error|string} error - Error object or message
   * @param {Object} context - Additional context for logging
   * @param {boolean} displayToast - Whether to show user notification
   * @returns {Promise} - Rejected promise with the error
   */
  handleError(error, context = {}, displayToast = true) {
    // Log to console
    console.error('Error occurred:', error, 'Context:', context);
    
    // Extract error message
    const errorMessage = this.formatErrorMessage(error);
    
    // Log to server
    this.logToServer(errorMessage, error, context);
    
    // Show toast notification if requested
    if (displayToast && this.dashboard.uiController) {
      this.dashboard.uiController.showToast(errorMessage, 'error');
    }
    
    // Return rejected promise to maintain chain
    return $.Deferred().reject(error);
  }
  
  /**
   * Format error message for display
   * @param {*} error - Error object or message
   * @returns {string} - Formatted message
   */
  formatErrorMessage(error) {
    if (typeof error === 'string') return error;
    if (error && error.message) return error.message;
    if (error && error.responseJSON && error.responseJSON.error) return error.responseJSON.error;
    if (error && error.statusText) return `Server error: ${error.statusText}`;
    return 'An unexpected error occurred';
  }
  
  /**
   * Log error to server
   * @param {string} message - Error message
   * @param {*} originalError - Original error object
   * @param {Object} context - Additional context
   */
  logToServer(message, originalError, context) {
    const errorData = {
      message: message,
      context: context,
      error: originalError ? originalError.toString() : 'Unknown error',
      stack: originalError && originalError.stack ? originalError.stack : 'No stack trace',
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };
    
    // Use fetch for fire-and-forget logging
    fetch('/api/log-client-error', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(errorData),
      // Prevent error handler for this request to avoid infinite loop
      credentials: 'same-origin'
    }).catch(e => console.error('Failed to send error log:', e));
  }
  
  /**
   * Handle global JS errors
   * @param {ErrorEvent} event - Error event
   * @returns {boolean} - Whether to prevent default handling
   */
  handleGlobalError(event) {
    const errorDetails = {
      message: event.message || 'Unknown JavaScript error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error ? event.error.stack : 'No stack trace',
      type: 'global_error'
    };
    
    this.logToServer(errorDetails.message, event.error, errorDetails);
    
    // Don't prevent default error handling so browser console still shows error
    return false;
  }
}

/**
 * State Manager Class
 * Manages application state
 */
class StateManager {
  constructor() {
    this.isRefreshing = false;
    this.lastRefreshTime = null;
    this.pendingActions = new Map();
    this.activeFilters = {
      search: '',
      model: 'all',
      status: 'all'
    };
    this.autoRefreshPaused = false;
    this.currentAnalysis = null;
    this.pendingRequests = 0;
  }
  
  /**
   * Track pending action state
   * @param {string} actionKey - Unique action identifier
   * @param {boolean} isPending - Whether action is pending
   */
  setActionPending(actionKey, isPending) {
    if (isPending) {
      this.pendingActions.set(actionKey, true);
    } else {
      this.pendingActions.delete(actionKey);
    }
  }
  
  /**
   * Check if action is pending
   * @param {string} actionKey - Action identifier
   * @returns {boolean} - Whether action is pending
   */
  isActionPending(actionKey) {
    return this.pendingActions.has(actionKey);
  }
  
  /**
   * Track API request count
   * @param {boolean} isStarting - Whether request is starting or ending
   */
  trackApiRequest(isStarting) {
    if (isStarting) {
      this.pendingRequests++;
    } else {
      this.pendingRequests = Math.max(0, this.pendingRequests - 1);
    }
  }
  
  /**
   * Check if any API requests are pending
   * @returns {boolean} - Whether any requests are pending
   */
  hasApiRequestsPending() {
    return this.pendingRequests > 0;
  }
}

/**
 * API Service Class
 * Centralized API request handling
 */
class ApiService {
  /**
   * @param {ConfigurationManager} config - Configuration instance
   * @param {ErrorHandler} errorHandler - Error handler instance
   */
  constructor(config, errorHandler) {
    this.config = config;
    this.errorHandler = errorHandler;
    this.pendingRequests = new Map();
  }
  
  /**
   * Perform API request with standard options
   * @param {string} endpoint - API endpoint
   * @param {Object} options - AJAX options
   * @returns {Promise} - Promise for the request
   */
  request(endpoint, options = {}) {
    // Validate endpoint
    if (!endpoint || endpoint.includes('/undefined')) {
      return this.errorHandler.handleError(
        new Error(`Invalid API endpoint: ${endpoint}`),
        { endpoint, options },
        options.suppressToast !== true
      );
    }
    
    // Default request options
    const requestOptions = {
      url: endpoint,
      method: options.method || 'GET',
      dataType: options.dataType || 'json',
      cache: options.cache !== undefined ? options.cache : false,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        ...options.headers
      },
      data: options.data,
      contentType: options.contentType,
      timeout: options.timeout || this.config.api.timeout
    };
    
    // Generate request ID
    const requestId = options.requestId || `${endpoint}_${Date.now()}`;
    
    // Cancel previous request with same ID if exists
    this.cancelRequest(requestId);
    
    // Perform request with retry support
    return this.fetchWithRetry(requestOptions, options.retries, requestId)
      .always(() => {
        // Remove from pending requests
        this.pendingRequests.delete(requestId);
      });
  }
  
  /**
   * Cancel pending request by ID
   * @param {string} requestId - Request identifier
   * @returns {boolean} - Whether a request was cancelled
   */
  cancelRequest(requestId) {
    if (this.pendingRequests.has(requestId)) {
      const xhr = this.pendingRequests.get(requestId);
      if (xhr && xhr.abort) {
        xhr.abort();
        this.pendingRequests.delete(requestId);
        return true;
      }
    }
    return false;
  }
  
  /**
   * Fetch with retry logic
   * @param {Object} options - AJAX options
   * @param {number|null} retries - Number of retries
   * @param {string} requestId - Request identifier
   * @returns {Promise} - Promise for the request
   */
  fetchWithRetry(options, retries = null, requestId) {
    if (retries === null) {
      retries = this.config.api.retryAttempts;
    }
    
    // Function to attempt the request
    const attemptRequest = (remainingRetries) => {
      const xhr = $.ajax(options);
      
      // Store XHR for potential cancellation
      this.pendingRequests.set(requestId, xhr);
      
      return xhr.fail((jqXHR, textStatus, errorThrown) => {
        // Don't retry if request was aborted
        if (textStatus === 'abort') {
          return $.Deferred().reject({ aborted: true });
        }
        
        // Don't retry if no retries left
        if (remainingRetries <= 0) {
          return $.Deferred().reject(errorThrown || jqXHR || textStatus);
        }
        
        console.warn(
          `API request attempt failed (${this.config.api.retryAttempts - remainingRetries + 1}/${this.config.api.retryAttempts}):`, 
          textStatus
        );
        
        // Wait before retry using exponential backoff
        const delay = this.config.api.retryDelay * Math.pow(2, this.config.api.retryAttempts - remainingRetries);
        
        return new Promise(resolve => setTimeout(resolve, delay))
          .then(() => {
            return attemptRequest(remainingRetries - 1);
          });
      });
    };
    
    return attemptRequest(retries);
  }
  
  /**
   * Perform GET request
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Additional options
   * @returns {Promise} - Promise for the request
   */
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }
  
  /**
   * Perform POST request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request payload
   * @param {Object} options - Additional options
   * @returns {Promise} - Promise for the request
   */
  post(endpoint, data = {}, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      data: options.contentType === 'application/json' ? JSON.stringify(data) : data
    });
  }
}

/**
 * Utility Service Class
 * Provides helper functions
 */
class UtilityService {
  /**
   * @param {ErrorHandler} errorHandler - Error handler instance
   */
  constructor(errorHandler) {
    this.errorHandler = errorHandler;
  }

  /**
   * Create a debounced function
   * @param {Function} func - Function to debounce
   * @param {number} wait - Wait time in milliseconds
   * @returns {Function} - Debounced function
   */
  debounce(func, wait) {
    let timeout;
    return function() {
      const context = this;
      const args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        func.apply(context, args);
      }, wait);
    };
  }

  /**
   * Create a throttled function
   * @param {Function} func - Function to throttle
   * @param {number} limit - Throttle limit in milliseconds
   * @returns {Function} - Throttled function
   */
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const context = this;
      const args = arguments;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * Capitalize first letter of a string
   * @param {string} string - String to capitalize
   * @returns {string} - Capitalized string
   */
  capitalizeFirst(string) {
    if (!string) return '';
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  /**
   * Format bytes to human-readable string
   * @param {number} bytes - Bytes to format
   * @param {number} decimals - Decimal places
   * @returns {string} - Formatted string
   */
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
  }

  /**
   * Format seconds to human-readable uptime
   * @param {number} seconds - Seconds to format
   * @returns {string} - Formatted uptime string
   */
  formatUptime(seconds) {
    if (seconds === undefined || seconds === null) return 'Unknown';
    
    const days = Math.floor(seconds / 86400);
    seconds %= 86400;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    
    let result = '';
    if (days > 0) result += `${days}d `;
    if (hours > 0 || days > 0) result += `${hours}h `;
    result += `${minutes}m`;
    
    return result;
  }
  
  /**
   * Format date/time to locale string
   * @param {Date|string|number} date - Date to format
   * @param {Object} options - Format options
   * @returns {string} - Formatted date string
   */
  formatDateTime(date, options = {}) {
    if (!date) return '';
    
    try {
      const dateObj = date instanceof Date ? date : new Date(date);
      return dateObj.toLocaleString(undefined, {
        dateStyle: options.dateStyle || 'short',
        timeStyle: options.timeStyle || 'medium',
        ...options
      });
    } catch (e) {
      this.errorHandler.handleError(e, { date }, false);
      return String(date);
    }
  }
  
  /**
   * Generate unique ID
   * @param {string} prefix - Optional prefix
   * @returns {string} - Unique ID
   */
  generateId(prefix = 'id') {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Safely parse JSON
   * @param {string} jsonString - JSON string to parse
   * @param {*} fallbackValue - Value to return if parsing fails
   * @returns {*} - Parsed object or fallback value
   */
  safeJsonParse(jsonString, fallbackValue = null) {
    try {
      return JSON.parse(jsonString);
    } catch (e) {
      console.warn('JSON parse error:', e);
      return fallbackValue;
    }
  }
}

/**
 * UI Service Class
 * Handles UI utilities and element manipulation
 */
class UIService {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    this.toastContainer = null;
    this.toastQueue = [];
    this.isProcessingToasts = false;
  }
  
  /**
   * Update element text content
   * @param {string|Element} selector - Element selector or DOM element
   * @param {*} value - New content value
   * @param {Function} formatFn - Optional formatting function
   * @returns {boolean} - Success status
   */
  updateElement(selector, value, formatFn = null) {
    const $element = selector instanceof Element ? $(selector) : $(selector);
    if (!$element.length) return false;
    
    const displayValue = formatFn ? formatFn(value) : value;
    $element.text(displayValue);
    return true;
  }
  
  /**
   * Update element with class based on thresholds
   * @param {string|Element} selector - Element selector or DOM element
   * @param {*} value - Value to check against thresholds
   * @param {Object} classConfig - Class configuration
   * @returns {boolean} - Success status
   */
  updateElementWithClass(selector, value, classConfig) {
    const $element = selector instanceof Element ? $(selector) : $(selector);
    if (!$element.length) return false;
    
    // Find appropriate class from thresholds
    let className = classConfig.default || '';
    
    if (classConfig.thresholds) {
      // Sort thresholds in descending order to check highest first
      const thresholds = [...classConfig.thresholds].sort((a, b) => 
        (b.threshold === undefined ? -Infinity : b.threshold) - 
        (a.threshold === undefined ? -Infinity : a.threshold)
      );
      
      // Find first matching threshold
      for (const threshold of thresholds) {
        if (threshold.threshold === undefined || value > threshold.threshold) {
          className = threshold.class;
          break;
        }
      }
    }
    
    // Update class
    $element.attr('class', className);
    return true;
  }
  
  /**
   * Show loading indicator
   * @param {Element} element - Element to show loading in
   * @param {string} text - Loading text
   * @returns {Function} - Function to hide loading indicator
   */
  showLoading(element, text = 'Loading...') {
    const $element = $(element);
    if (!$element.length) return () => {};
    
    // Store original content and disabled state
    const originalContent = $element.html();
    const wasDisabled = $element.prop('disabled');
    
    // Create spinner
    const spinner = `
      <svg class="inline-block w-4 h-4 mr-1 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    `;
    
    // Update element
    $element.html(spinner + text);
    $element.prop('disabled', true);
    
    // Return function to restore original state
    return () => {
      $element.html(originalContent);
      $element.prop('disabled', wasDisabled);
    };
  }
  
  /**
   * Show toast notification
   * @param {string} message - Message to display
   * @param {string} type - Notification type (success, error, info)
   * @param {Object} options - Additional options
   * @returns {Element} - Toast element
   */
  showToast(message, type = 'success', options = {}) {
    if (!message) return null;
    
    // Create toast container if needed
    if (!this.toastContainer) {
      this.toastContainer = $('<div>', {
        id: 'toastContainer',
        class: 'fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none'
      }).appendTo('body')[0];
    }
    
    // Determine toast style based on type
    const toastClasses = 
      type === 'success' ? 'bg-green-100 border border-green-300 text-green-800' :
      type === 'error' ? 'bg-red-100 border border-red-300 text-red-800' :
      type === 'warning' ? 'bg-yellow-100 border border-yellow-300 text-yellow-800' :
      'bg-blue-100 border border-blue-300 text-blue-800';
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `px-4 py-2 rounded-sm shadow-md text-sm transition-opacity duration-300 opacity-0 pointer-events-auto ${toastClasses}`;
    toast.textContent = message;
    
    // Add dismiss button if not auto-dismiss
    if (options.autoDismiss === false) {
      const dismissBtn = document.createElement('button');
      dismissBtn.className = 'ml-2 text-gray-600 hover:text-gray-800';
      dismissBtn.innerHTML = '&times;';
      dismissBtn.addEventListener('click', () => {
        this.dismissToast(toast);
      });
      toast.appendChild(dismissBtn);
    }
    
    // Add to queue
    this.toastQueue.push({
      element: toast,
      duration: options.duration || this.dashboard.config.ui.toastDuration
    });
    
    // Process queue
    this.processToastQueue();
    
    return toast;
  }
  
  /**
   * Process toast notification queue
   */
  processToastQueue() {
    if (this.isProcessingToasts || this.toastQueue.length === 0) return;
    
    this.isProcessingToasts = true;
    
    // Get next toast from queue
    const { element, duration } = this.toastQueue.shift();
    
    // Add to container
    this.toastContainer.appendChild(element);
    
    // Show with animation
    setTimeout(() => {
      element.classList.add('opacity-100');
      
      // Auto-dismiss after duration
      if (duration > 0) {
        setTimeout(() => {
          this.dismissToast(element);
        }, duration);
      }
    }, 10);
  }
  
  /**
   * Dismiss toast notification
   * @param {Element} toast - Toast element to dismiss
   */
  dismissToast(toast) {
    // Hide with animation
    toast.classList.remove('opacity-100');
    toast.classList.add('opacity-0');
    
    // Remove after animation
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      
      // Process next toast
      this.isProcessingToasts = false;
      this.processToastQueue();
    }, 300);
  }
  
  /**
   * Toggle element visibility
   * @param {string|Element} selector - Element selector or DOM element
   * @param {boolean} isVisible - Whether element should be visible
   * @returns {boolean} - Success status
   */
  toggleVisibility(selector, isVisible) {
    const $element = selector instanceof Element ? $(selector) : $(selector);
    if (!$element.length) return false;
    
    $element.toggle(isVisible);
    return true;
  }
  
  /**
   * Create loading indicator HTML
   * @param {string} text - Loading text
   * @returns {string} - HTML for loading indicator
   */
  getLoadingIndicator(text = 'Loading') {
    return `
      <svg class="inline-block w-4 h-4 mr-1 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>${text}...
    `;
  }
}

/**
 * Polling Service Class
 * Manages polling for data updates
 */
class PollingService {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    this.activePolls = new Map();
  }
  
  /**
   * Start polling an endpoint
   * @param {string} id - Unique poll identifier
   * @param {string} endpoint - Endpoint to poll
   * @param {Object} options - Polling options
   * @returns {string} - Poll ID
   */
  startPolling(id, endpoint, options = {}) {
    // Ensure we have a valid ID
    const pollId = id || this.dashboard.utilityService.generateId('poll');
    
    // Stop existing poll if it exists
    this.stopPolling(pollId);
    
    // Configure poll
    const config = {
      interval: options.interval || 2000,
      maxErrorCount: options.maxErrorCount || 3,
      onSuccess: options.onSuccess || (() => {}),
      onError: options.onError || (() => {}),
      onComplete: options.onComplete || (() => {}),
      completionCheck: options.completionCheck || (() => false),
      requestOptions: options.requestOptions || {}
    };
    
    let errorCount = 0;
    
    // Create polling function
    const doPoll = () => {
      if (!this.activePolls.has(pollId)) return;
      
      this.dashboard.apiService.request(endpoint, {
        ...config.requestOptions,
        suppressToast: true,
        requestId: `poll_${pollId}`
      })
      .done(data => {
        // Reset error count on success
        errorCount = 0;
        
        // Call success handler
        config.onSuccess(data);
        
        // Check if polling should complete
        if (config.completionCheck(data)) {
          this.stopPolling(pollId);
          config.onComplete(data);
          return;
        }
        
        // Schedule next poll if still active
        if (this.activePolls.has(pollId)) {
          const timerId = setTimeout(doPoll, config.interval);
          this.activePolls.set(pollId, timerId);
        }
      })
      .fail(error => {
        // Skip error handling for aborted requests
        if (error && error.aborted) return;
        
        errorCount++;
        
        // Call error handler
        config.onError(error, errorCount);
        
        // Stop polling if too many errors
        if (errorCount >= config.maxErrorCount) {
          this.stopPolling(pollId);
          return;
        }
        
        // Schedule next poll with increased delay if still active
        if (this.activePolls.has(pollId)) {
          const backoffDelay = config.interval * Math.pow(2, errorCount);
          const timerId = setTimeout(doPoll, backoffDelay);
          this.activePolls.set(pollId, timerId);
        }
      });
    };
    
    // Start polling immediately
    const timerId = setTimeout(doPoll, 0);
    this.activePolls.set(pollId, timerId);
    
    return pollId;
  }
  
  /**
   * Stop polling by ID
   * @param {string} id - Poll ID
   * @returns {boolean} - Whether poll was stopped
   */
  stopPolling(id) {
    if (this.activePolls.has(id)) {
      clearTimeout(this.activePolls.get(id));
      this.activePolls.delete(id);
      
      // Cancel any in-flight requests
      this.dashboard.apiService.cancelRequest(`poll_${id}`);
      
      return true;
    }
    return false;
  }
  
  /**
   * Stop all active polling
   */
  stopAllPolling() {
    for (const [id, timerId] of this.activePolls.entries()) {
      clearTimeout(timerId);
      
      // Cancel any in-flight requests
      this.dashboard.apiService.cancelRequest(`poll_${id}`);
    }
    
    this.activePolls.clear();
  }
}

/**
 * Core Controller Class
 * Manages core application functionality
 */
class CoreController {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    this.autoRefreshService = new AutoRefreshService(dashboard);
    this.systemInfoService = new SystemInfoService(dashboard);
  }

  /**
   * Initialize core functionality
   */
  init() {
    this.autoRefreshService.setup();
    this.systemInfoService.init();
  }

  /**
   * Refresh all app statuses
   */
  refreshAllStatuses() {
    if (this.dashboard.stateManager.isRefreshing) return;
    
    this.dashboard.stateManager.isRefreshing = true;
    
    try {
      // Get all model sections
      $('[data-model-section]').each((i, section) => {
        const model = $(section).data('model-section');
        if (!model) return;
        
        // Get all app cards for this model
        $(`[data-model="${model}"][data-app-id]`, section).each((j, card) => {
          const appNum = $(card).data('app-id');
          if (!appNum) return;
          
          this.updateAppStatus(model, appNum);
        });
      });
      
      // Update refresh timestamp
      this.dashboard.stateManager.lastRefreshTime = new Date();
      this.dashboard.uiController.updateRefreshTimestamp();
    } catch (error) {
      this.dashboard.errorHandler.handleError(error, {
        action: 'refreshAllStatuses'
      }, true);
    } finally {
      this.dashboard.stateManager.isRefreshing = false;
    }
  }

  /**
   * Update status for a specific app
   * @param {string} model - Model name
   * @param {string|number} appNum - App number
   * @returns {Promise} - Promise for the status update
   */
  updateAppStatus(model, appNum) {
    if (!model || !appNum) {
      return $.Deferred().reject(new Error('Invalid parameters'));
    }
    
    return this.dashboard.apiService.get(`/status/${model}/${appNum}`)
      .done(data => {
        this.dashboard.uiController.updateStatusDisplay(model, appNum, data);
      })
      .fail(error => {
        console.error(`Error updating status for ${model} app ${appNum}:`, error);
      });
  }

  /**
   * Perform an action on an app
   * @param {string} action - Action to perform (start, stop, reload, etc.)
   * @param {string} model - Model name
   * @param {string|number} appNum - App number
   * @returns {Promise} - Promise for the action
   */
  performAppAction(action, model, appNum) {
    if (!action || !model || !appNum) {
      return $.Deferred().reject('Missing required parameters for action');
    }
    
    // Special handling for rebuild which may take longer
    if (action === 'rebuild') {
      this.dashboard.uiController.showToast(
        `Rebuilding ${model} App ${appNum}. This may take several minutes...`, 
        'info'
      );
    }
    
    return this.dashboard.apiService.post(`/${action}/${model}/${appNum}`)
      .done(result => {
        if (result && result.message) {
          console.log(`${action} result:`, result.message);
        }
        return true;
      })
      .fail(error => {
        throw new Error(`Failed to ${action}: ${error}`);
      });
  }

  /**
   * Perform batch operation on multiple apps
   * @param {string} action - Action to perform
   * @param {string} model - Model name
   * @returns {Promise} - Promise for the batch operation
   */
  performBatchOperation(action, model) {
    if (!action || !model) {
      return $.Deferred().reject('Missing required parameters for batch operation');
    }
    
    const $modelSection = $(`[data-model-section="${model}"]`);
    if ($modelSection.length === 0) {
      return $.Deferred().reject(`Model section not found for ${model}`);
    }
    
    // Find all apps for this model
    const $appCards = $(`[data-model="${model}"][data-app-id]`, $modelSection);
    if ($appCards.length === 0) {
      return $.Deferred().reject(`No apps found for model ${model}`);
    }
    
    // Get app numbers
    const appNumbers = $.map($appCards, function(card) {
      return $(card).data('app-id');
    }).filter(Boolean);
    
    // Process results
    const results = { 
      success: 0, 
      failed: 0, 
      processed: 0, 
      total: appNumbers.length 
    };
    
    const deferred = $.Deferred();
    
    // Process apps in batches
    this.processBatchesSequentially(action, model, appNumbers, results, deferred);
    
    return deferred.promise();
  }

  /**
   * Process batches sequentially
   * @param {string} action - Action to perform
   * @param {string} model - Model name
   * @param {Array} appNumbers - Array of app numbers
   * @param {Object} results - Results object
   * @param {Object} deferred - Deferred object
   */
  processBatchesSequentially(action, model, appNumbers, results, deferred) {
    const batchSize = 3;
    const batchPromises = [];
    
    // Create batch promises
    for (let i = 0; i < appNumbers.length; i += batchSize) {
      const batch = appNumbers.slice(i, i + batchSize);
      
      const processBatch = () => {
        const promises = batch.map(appNum => {
          return this.processBatchOperation(action, model, appNum)
            .then(success => {
              results.processed++;
              if (success) results.success++;
              else results.failed++;
              
              // Update UI with progress
              this.dashboard.uiController.updateBatchProgress(
                model, action, results.processed, results.total
              );
              
              return success;
            });
        });
        
        return $.when.apply($, promises);
      };
      
      batchPromises.push(processBatch);
    }
    
    // Execute batches sequentially
    let chain = $.Deferred().resolve();
    batchPromises.forEach(batchFn => {
      chain = chain.then(batchFn);
    });
    
    // When all batches are done
    chain.then(() => {
      // Update final status
      this.dashboard.uiController.updateBatchResult(
        model, action, results.success, results.failed, results.total
      );
      
      // Refresh statuses
      setTimeout(() => {
        this.refreshAllStatuses();
      }, 1000);
      
      deferred.resolve(results);
    }).fail(error => {
      this.dashboard.errorHandler.handleError(error, {
        action: 'batchOperation',
        model,
        appNumbers
      });
      deferred.reject(error);
    });
  }

  /**
   * Process single batch operation
   * @param {string} action - Action to perform
   * @param {string} model - Model name
   * @param {string|number} appNum - App number
   * @returns {Promise<boolean>} - Promise resolving to success state
   */
  processBatchOperation(action, model, appNum) {
    if (!model || !appNum || !action) {
      console.error('Invalid batch operation parameters', { model, appNum, action });
      return $.Deferred().resolve(false);
    }
    
    // Handle special non-Docker actions
    if (action === 'health-check') {
      return this.dashboard.apiService.get(`/api/health/${model}/${appNum}`)
        .then(() => true)
        .fail(() => false);
    }
    
    // Handle standard actions with retry logic
    return this.dashboard.apiService.post(`/${action}/${model}/${appNum}`)
      .then(() => true)
      .fail(() => false);
  }
}

/**
 * Auto-Refresh Service Class
 * Manages periodic status updates
 */
class AutoRefreshService {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }

  /**
   * Set up auto-refresh based on configuration
   */
  setup() {
    if (this.dashboard.config.autoRefresh.enabled) {
      this.start();
    }
  }

  /**
   * Start auto-refresh timer
   */
  start() {
    if (this.dashboard.config.autoRefresh.timer) return;
    
    this.dashboard.config.autoRefresh.enabled = true;
    this.dashboard.config.autoRefresh.timer = setInterval(() => {
      this.dashboard.coreController.refreshAllStatuses();
    }, this.dashboard.config.autoRefresh.interval);
    
    this.dashboard.config.saveSettings();
    this.dashboard.uiController.updateAutoRefreshDisplay(true);
  }

  /**
   * Stop auto-refresh timer
   */
  stop() {
    if (this.dashboard.config.autoRefresh.timer) {
      clearInterval(this.dashboard.config.autoRefresh.timer);
      this.dashboard.config.autoRefresh.timer = null;
    }
    
    this.dashboard.config.autoRefresh.enabled = false;
    this.dashboard.config.saveSettings();
    this.dashboard.uiController.updateAutoRefreshDisplay(false);
  }

  /**
   * Toggle auto-refresh state
   */
  toggle() {
    if (this.dashboard.config.autoRefresh.enabled) {
      this.stop();
    } else {
      this.start();
    }
  }

  /**
   * Pause auto-refresh temporarily
   */
  pause() {
    if (this.dashboard.config.autoRefresh.timer) {
      clearInterval(this.dashboard.config.autoRefresh.timer);
      this.dashboard.config.autoRefresh.timer = null;
      this.dashboard.stateManager.autoRefreshPaused = true;
    }
  }

  /**
   * Resume auto-refresh if it was paused
   */
  resume() {
    if (this.dashboard.stateManager.autoRefreshPaused && 
        this.dashboard.config.autoRefresh.enabled) {
      this.dashboard.config.autoRefresh.timer = setInterval(() => {
        this.dashboard.coreController.refreshAllStatuses();
      }, this.dashboard.config.autoRefresh.interval);
      this.dashboard.stateManager.autoRefreshPaused = false;
    }
  }
}

/**
 * System Info Service Class
 * Handles system information retrieval and updates
 */
class SystemInfoService {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }

  /**
   * Initialize system info service
   */
  init() {
    this.load();
    // Refresh system info periodically (every 60s)
    setInterval(this.load.bind(this), 60000);
  }

  /**
   * Load system information from API
   */
  load() {
    this.dashboard.apiService.get('/api/system-info')
      .done(data => {
        this.dashboard.uiController.updateSystemInfoDisplay(data);
      })
      .fail(error => {
        console.error('Failed to load system info:', error);
      });
  }
}

/**
 * UI Controller Class
 * Manages UI interactions and updates
 */
class UIController {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    
    // Element selector mapping for easier maintenance
    this.selectors = {
      actionButtons: '.action-btn',
      refreshAllBtn: '#refreshAll',
      toggleAutorefreshBtn: '#toggleAutorefresh',
      autorefreshText: '#autorefreshText',
      appCards: '[data-app-id]',
      searchInput: '#searchApps',
      modelFilter: '#filterModel',
      statusFilter: '#filterStatus',
      noResultsMessage: '#noResultsMessage',
      lastRefreshTime: '#lastRefreshTime',
      batchMenu: '.batch-menu-button',
      batchMenuItems: '.batch-menu-items',
      batchAction: '.batch-action'
    };
  }

  /**
   * Initialize UI controller
   */
  init() {
    this.setupEventListeners();
    this.setupFilters();
    this.updateAutoRefreshDisplay(this.dashboard.config.autoRefresh.enabled);
  }

  /**
   * Set up UI event listeners
   */
  setupEventListeners() {
    this.setupActionButtons();
    this.setupRefreshButtons();
    this.setupBatchMenuButtons();
    this.setupDocumentClicks();
  }

  /**
   * Set up action button event listeners
   */
  setupActionButtons() {
    // Action buttons
    this.dashboard.eventManager.on(document, 'click', this.selectors.actionButtons, e => {
      this.handleActionButton(e);
    });
  }

  /**
   * Set up refresh button event listeners
   */
  setupRefreshButtons() {
    // Refresh all button
    this.dashboard.eventManager.on(document, 'click', this.selectors.refreshAllBtn, () => {
      this.dashboard.coreController.refreshAllStatuses();
    });
    
    // Toggle auto-refresh button
    this.dashboard.eventManager.on(document, 'click', this.selectors.toggleAutorefreshBtn, () => {
      this.dashboard.coreController.autoRefreshService.toggle();
    });
  }

  /**
   * Set up batch menu button event listeners
   */
  setupBatchMenuButtons() {
    // Batch menu buttons
    this.dashboard.eventManager.on(document, 'click', this.selectors.batchMenu, e => {
      e.stopPropagation();
      const $dropdown = $(e.currentTarget).next(this.selectors.batchMenuItems);
      
      $dropdown.toggleClass('hidden');
      
      // Close other open dropdowns
      $(this.selectors.batchMenuItems).not($dropdown).addClass('hidden');
    });
    
    // Batch action buttons
    this.dashboard.eventManager.on(document, 'click', this.selectors.batchAction, e => {
      this.handleBatchAction(e);
    });
  }

  /**
   * Set up document-level click handler to close dropdowns
   */
  setupDocumentClicks() {
    // Close dropdowns when clicking elsewhere
    this.dashboard.eventManager.on(document, 'click', () => {
      $(this.selectors.batchMenuItems).addClass('hidden');
    });
  }

  /**
   * Set up filter functionality
   */
  setupFilters() {
    const $searchInput = $(this.selectors.searchInput);
    const $modelFilter = $(this.selectors.modelFilter);
    const $statusFilter = $(this.selectors.statusFilter);
    
    if ($searchInput.length) {
      $searchInput.on('input', this.dashboard.utilityService.debounce(() => {
        this.filterApps();
      }, 300));
    }
    
    if ($modelFilter.length) {
      $modelFilter.on('change', () => {
        this.filterApps();
      });
    }
    
    if ($statusFilter.length) {
      $statusFilter.on('change', () => {
        this.filterApps();
      });
    }
  }

  /**
   * Filter applications based on search and dropdown filters
   */
  filterApps() {
    const $searchInput = $(this.selectors.searchInput);
    const $modelFilter = $(this.selectors.modelFilter);
    const $statusFilter = $(this.selectors.statusFilter);
    
    if (!$searchInput.length && !$modelFilter.length && !$statusFilter.length) return;
    
    const searchTerm = $searchInput.length ? $searchInput.val().toLowerCase() : '';
    const modelValue = $modelFilter.length ? $modelFilter.val() : 'all';
    const statusValue = $statusFilter.length ? $statusFilter.val() : 'all';
    
    // Update active filters
    this.dashboard.stateManager.activeFilters = {
      search: searchTerm,
      model: modelValue,
      status: statusValue
    };
    
    // Apply filters to app cards
    let visibleCount = 0;
    
    $(this.selectors.appCards).each((i, card) => {
      const $card = $(card);
      const model = $card.data('model') || '';
      const appName = $card.data('appName') || '';
      const appId = $card.data('appId') || '';
      const status = $card.data('status') || '';
      
      const matchesSearch = !searchTerm || 
                         appName.toLowerCase().includes(searchTerm) || 
                         appId.toString().includes(searchTerm) ||
                         model.toLowerCase().includes(searchTerm);
      const matchesModel = modelValue === 'all' || modelValue === '' || model === modelValue;
      const matchesStatus = statusValue === 'all' || statusValue === '' || status === statusValue;
      
      const isVisible = matchesSearch && matchesModel && matchesStatus;
      $card.toggle(isVisible);
      if (isVisible) visibleCount++;
    });
    
    this.toggleNoResultsMessage(visibleCount === 0);
  }

  /**
   * Show/hide no results message
   * @param {boolean} show - Whether to show the message
   */
  toggleNoResultsMessage(show) {
    const $noResultsMessage = $(this.selectors.noResultsMessage);
    if ($noResultsMessage.length) {
      $noResultsMessage.toggle(show);
    }
  }

  /**
   * Handle action button click
   * @param {Event} event - Click event
   */
  handleActionButton(event) {
    const button = event.currentTarget;
    const action = button.dataset.action;
    const model = button.dataset.model;
    const appNum = button.dataset.appNum;
    
    if (!action || !model || !appNum) {
      console.error('Missing required data attributes on button', button);
      this.showToast('Invalid button configuration', 'error');
      return;
    }
    
    // Prevent duplicate actions
    const actionKey = `${action}-${model}-${appNum}`;
    if (this.dashboard.stateManager.isActionPending(actionKey)) {
      console.log(`Action ${actionKey} already in progress, skipping`);
      return;
    }
    
    // Add to pending actions
    const originalText = button.textContent;
    this.dashboard.stateManager.setActionPending(actionKey, true);
    
    // Update button state
    button.disabled = true;
    button.innerHTML = this.dashboard.uiService.getLoadingIndicator(
      this.dashboard.utilityService.capitalizeFirst(action)
    );
    
    // Perform the action
    this.dashboard.coreController.performAppAction(action, model, appNum)
      .then(() => {
        // Update app status after action
        return this.dashboard.coreController.updateAppStatus(model, appNum);
      })
      .then(() => {
        // Show success message
        this.showToast(`${this.dashboard.utilityService.capitalizeFirst(action)} operation successful`);
      })
      .fail(error => {
        this.showToast(`Failed to ${action}: ${error.message || error}`, 'error');
        this.dashboard.errorHandler.handleError(
          error,
          { action, model, appNum },
          false  // Don't show duplicate toast
        );
      })
      .always(() => {
        // Restore button state
        button.disabled = false;
        button.textContent = originalText;
        
        // Remove from pending actions
        this.dashboard.stateManager.setActionPending(actionKey, false);
      });
  }

  /**
   * Handle batch action button click
   * @param {Event} event - Click event
   */
  handleBatchAction(event) {
    const button = event.currentTarget;
    const action = button.dataset.action;
    const model = button.dataset.model;
    
    if (!action || !model) {
      console.error('Missing required data attributes on batch button', button);
      this.showToast('Invalid batch button configuration', 'error');
      return;
    }
    
    // Close the dropdown menu
    button.closest(this.selectors.batchMenuItems).classList.add('hidden');
    
    // Confirm the batch operation
    if (!confirm(`Are you sure you want to ${action} all apps for model ${model}?`)) {
      return;
    }
    
    // Show batch operation starting
    this.showBatchStatus(model, action, 'starting');
    
    // Perform batch operation
    this.dashboard.coreController.performBatchOperation(action, model)
      .done(result => {
        // Show success message
        if (result.failed === 0) {
          this.showToast(`All ${model} apps ${action}ed successfully`);
        } else if (result.success === 0) {
          this.showToast(`Failed to ${action} any ${model} apps`, 'error');
        } else {
          this.showToast(`${result.success} succeeded, ${result.failed} failed`, 'warning');
        }
      })
      .fail(error => {
        this.showToast(`Batch operation failed: ${error.message || error}`, 'error');
        this.showBatchStatus(model, action, 'failed');
        
        this.dashboard.errorHandler.handleError(
          error,
          { 
            action: 'batchOperation',
            batchAction: action,
            model
          },
          false  // Don't show duplicate toast
        );
      });
  }

  /**
   * Update status display for an app
   * @param {string} model - Model name
   * @param {string|number} appNum - App number
   * @param {Object} data - Status data
   */
  updateStatusDisplay(model, appNum, data) {
    if (!model || !appNum || !data) return;
    
    const $appCard = $(`[data-model="${model}"][data-app-id="${appNum}"]`);
    if ($appCard.length === 0) return;
    
    try {
      this.updateStatusElements($appCard, data);
      this.updateLastUpdateTimestamp($appCard);
      
      // Update metrics if available
      if (data.metrics) {
        this.updateMetricsDisplay($appCard, data.metrics);
      }
    } catch (error) {
      this.dashboard.errorHandler.handleError(
        error,
        { 
          action: 'updateStatusDisplay', 
          model, 
          appNum, 
          dataKeys: data ? Object.keys(data) : null
        },
        false  // Don't show toast for UI updates
      );
    }
  }

  /**
   * Update status elements within an app card
   * @param {jQuery} $appCard - App card jQuery element
   * @param {Object} data - Status data
   */
  updateStatusElements($appCard, data) {
    // Backend status
    const $backendStatusEl = $appCard.find('[data-status="backend"]');
    if ($backendStatusEl.length) {
      $backendStatusEl.text(data.backend_status?.running ? 'Running' : 'Stopped');
      $backendStatusEl.attr('class', data.backend_status?.running ? 'font-medium text-green-700' : 'font-medium text-red-700');
    }
    
    // Frontend status
    const $frontendStatusEl = $appCard.find('[data-status="frontend"]');
    if ($frontendStatusEl.length) {
      $frontendStatusEl.text(data.frontend_status?.running ? 'Running' : 'Stopped');
      $frontendStatusEl.attr('class', data.frontend_status?.running ? 'font-medium text-green-700' : 'font-medium text-red-700');
    }
    
    // Overall status badge
    const $statusBadgeEl = $appCard.find('.status-badge');
    if ($statusBadgeEl.length) {
      const isBackendRunning = data.backend_status?.running || false;
      const isFrontendRunning = data.frontend_status?.running || false;
      
      let status, classes;
      if (isBackendRunning && isFrontendRunning) {
        status = 'Running';
        classes = 'status-badge text-xs px-1 border rounded-sm bg-green-100 text-green-800 border-green-700';
      } else if (isBackendRunning || isFrontendRunning) {
        status = 'Partial';
        classes = 'status-badge text-xs px-1 border rounded-sm bg-yellow-100 text-yellow-800 border-yellow-700';
      } else {
        status = 'Stopped';
        classes = 'status-badge text-xs px-1 border rounded-sm bg-red-100 text-red-800 border-red-700';
      }
      
      $statusBadgeEl.text(status);
      $statusBadgeEl.attr('class', classes);
      
      // Update app card status attribute for filtering
      $appCard.data('status', status.toLowerCase());
    }
  }

  /**
   * Update the last updated timestamp on an app card
   * @param {jQuery} $appCard - App card jQuery element
   */
  updateLastUpdateTimestamp($appCard) {
    const $lastUpdateEl = $appCard.find('[data-last-update]');
    if ($lastUpdateEl.length) {
      const now = new Date();
      $lastUpdateEl.text(`Last updated: ${now.toLocaleTimeString()}`);
      $lastUpdateEl.data('timestamp', now.getTime());
    }
  }

  /**
   * Update metrics display for an app
   * @param {jQuery} $card - App card jQuery element
   * @param {Object} metrics - Metrics data
   */
  updateMetricsDisplay($card, metrics) {
    if (!$card || !metrics) return;
    
    // CPU usage
    const $cpuEl = $card.find('.metric-cpu');
    if ($cpuEl.length && metrics.cpu_percent !== undefined) {
      $cpuEl.text(`${metrics.cpu_percent.toFixed(1)}%`);
    }
    
    // Memory usage
    const $memEl = $card.find('.metric-memory');
    if ($memEl.length && metrics.memory_usage !== undefined) {
      $memEl.text(this.dashboard.utilityService.formatBytes(metrics.memory_usage));
    }
    
    // Request count
    const $requestsEl = $card.find('.metric-requests');
    if ($requestsEl.length && metrics.request_count !== undefined) {
      $requestsEl.text(metrics.request_count.toLocaleString());
    }
  }

  /**
   * Show batch operation status
   * @param {string} model - Model name
   * @param {string} action - Action being performed
   * @param {string} state - Current state
   */
  showBatchStatus(model, action, state = 'starting') {
    const $modelSection = $(`[data-model-section="${model}"]`);
    if ($modelSection.length === 0) return;
    
    const $statusEl = $modelSection.find('.batch-status');
    const $statusTextEl = $statusEl.find('.batch-status-text');
    
    if (!$statusEl.length || !$statusTextEl.length) return;
    
    // Show status element
    $statusEl.removeClass('hidden');
    
    // Set text based on state
    if (state === 'starting') {
      $statusTextEl.text(`${this.dashboard.utilityService.capitalizeFirst(action)}ing apps...`);
    } else if (state === 'failed') {
      $statusTextEl.text(`Failed to ${action} apps`);
      $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-red-100 text-red-800 border border-red-300 rounded-sm');
    }
  }

  /**
   * Update batch operation progress
   * @param {string} model - Model name
   * @param {string} action - Action being performed
   * @param {number} completed - Number of completed operations
   * @param {number} total - Total number of operations
   */
  updateBatchProgress(model, action, completed, total) {
    const $progressEl = $(`[data-model-section="${model}"] .batch-progress`);
    if ($progressEl.length) {
      $progressEl.text(`${completed}/${total}`);
    }
  }

  /**
   * Update batch operation result
   * @param {string} model - Model name
   * @param {string} action - Action performed
   * @param {number} success - Number of successful operations
   * @param {number} failed - Number of failed operations
   * @param {number} total - Total number of operations
   */
  updateBatchResult(model, action, success, failed, total) {
    const $modelSection = $(`[data-model-section="${model}"]`);
    if ($modelSection.length === 0) return;
    
    const $statusEl = $modelSection.find('.batch-status');
    const $statusTextEl = $statusEl.find('.batch-status-text');
    
    if (!$statusEl.length || !$statusTextEl.length) return;
    
    // Set text based on result
    if (failed === 0) {
      $statusTextEl.text(`All apps ${action}ed successfully`);
      $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-green-100 text-green-800 border border-green-300 rounded-sm');
      
      // Hide after delay
      setTimeout(() => {
        $statusEl.addClass('hidden');
      }, 5000);
    } else if (success === 0) {
      $statusTextEl.text(`Failed to ${action} all apps`);
      $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-red-100 text-red-800 border border-red-300 rounded-sm');
    } else {
      $statusTextEl.text(`${success} succeeded, ${failed} failed`);
      $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 border border-yellow-300 rounded-sm');
    }
  }

  /**
   * Update system information display
   * @param {Object} data - System info data
   */
  updateSystemInfoDisplay(data) {
    if (!data) return;
    
    // Update each system metric element
    this.updateSystemMetric('#systemCpuUsage', data.cpu_percent, '%', [
      { threshold: 80, class: 'text-red-600 font-medium' },
      { threshold: 50, class: 'text-yellow-600 font-medium' },
      { default: 'text-green-600 font-medium' }
    ]);
    
    this.updateSystemMetric('#systemMemoryUsage', data.memory_percent, '%', [
      { threshold: 85, class: 'text-red-600 font-medium' },
      { threshold: 70, class: 'text-yellow-600 font-medium' },
      { default: 'text-green-600 font-medium' }
    ]);
    
    this.updateSystemMetric('#systemDiskUsage', data.disk_percent, '%', [
      { threshold: 90, class: 'text-red-600 font-medium' },
      { threshold: 75, class: 'text-yellow-600 font-medium' },
      { default: 'text-green-600 font-medium' }
    ]);
    
    // System uptime
    const $uptimeEl = $('#systemUptime');
    if ($uptimeEl.length && data.uptime_seconds !== undefined) {
      $uptimeEl.text(this.dashboard.utilityService.formatUptime(data.uptime_seconds));
    }
  }

  /**
   * Update a system metric element
   * @param {string} selector - Element selector
   * @param {number} value - Metric value
   * @param {string} suffix - Value suffix
   * @param {Array} thresholds - Styling thresholds
   */
  updateSystemMetric(selector, value, suffix, thresholds) {
    this.dashboard.uiService.updateElement(
      selector, 
      value, 
      v => `${v.toFixed(1)}${suffix}`
    );
    
    this.dashboard.uiService.updateElementWithClass(
      selector, 
      value, 
      {
        default: thresholds[thresholds.length - 1].class,
        thresholds: thresholds.slice(0, -1)
      }
    );
  }

  /**
   * Update refresh timestamp display
   */
  updateRefreshTimestamp() {
    if (!this.dashboard.stateManager.lastRefreshTime) return;
    
    const $timestampEl = $(this.selectors.lastRefreshTime);
    if ($timestampEl.length) {
      $timestampEl.text(this.dashboard.stateManager.lastRefreshTime.toLocaleTimeString());
    }
  }

  /**
   * Update auto-refresh display based on state
   * @param {boolean} enabled - Whether auto-refresh is enabled
   */
  updateAutoRefreshDisplay(enabled) {
    const $toggleBtn = $(this.selectors.toggleAutorefreshBtn);
    const $statusText = $(this.selectors.autorefreshText);
    
    if ($toggleBtn.length) {
      $toggleBtn.text(enabled ? 'Disable Auto-Refresh' : 'Enable Auto-Refresh');
    }
    
    if ($statusText.length) {
      $statusText.text(enabled 
        ? `Auto Refresh: On (${this.dashboard.config.autoRefresh.interval/1000}s)` 
        : 'Auto Refresh: Off');
    }
  }

  /**
   * Show toast notification
   * @param {string} message - Message to display
   * @param {string} type - Notification type (success, error, info)
   * @param {Object} options - Additional options
   * @returns {Element} - Toast element
   */
  showToast(message, type = 'success', options = {}) {
    return this.dashboard.uiService.showToast(message, type, options);
  }
}

/**
 * Feature Manager Class
 * Manages feature-specific functionality
 */
class FeatureManager {
  /**
   * @param {Dashboard} dashboard - Main dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    
    // Feature instances
    this.features = {
      securityAnalysis: new SecurityAnalysis(dashboard),
      performanceTest: new PerformanceTest(dashboard),
      requirementsAnalysis: new RequirementsAnalysis(dashboard),
      securityAnalysisPage: new SecurityAnalysisPage(dashboard),
      zapScan: new ZapScan(dashboard)
    };
    
    // Feature detection map
    this.featureDetectors = {
      securityAnalysis: () => document.querySelector('.security-scan-btn') !== null,
      performanceTest: () => document.getElementById('runTest') !== null,
      requirementsAnalysis: () => document.querySelector('form') !== null && document.getElementById('submitBtn') !== null,
      securityAnalysisPage: () => document.getElementById('searchIssues') !== null && document.getElementById('riskFilter') !== null,
      zapScan: () => document.getElementById('startScan') !== null
    };
  }

  /**
   * Initialize features based on page elements
   */
  initFeatures() {
    // Detect and initialize only relevant features
    Object.entries(this.featureDetectors).forEach(([feature, detector]) => {
      if (detector() && this.features[feature]) {
        console.log(`Initializing feature: ${feature}`);
        this.features[feature].init();
      }
    });
  }
}

/**
 * Security Analysis Feature Class
 * Handles security analysis functionality
 */
class SecurityAnalysis {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }

  /**
   * Initialize security analysis functionality
   */
  init() {
    this.setupEventListeners();
    this.loadSecuritySummary();
  }

  /**
   * Set up event listeners for security analysis
   */
  setupEventListeners() {
    // Setup security scan buttons
    this.dashboard.eventManager.on(document, 'click', '.security-scan-btn', this.handleScanClick.bind(this));
    
    // Setup modal close buttons
    this.dashboard.eventManager.on(document, 'click', '.modal-close', () => {
      document.getElementById('securityModal').classList.add('hidden');
    });
    
    // Setup start analysis button
    this.dashboard.eventManager.on(document, 'click', '#startAnalysis', this.startAnalysis.bind(this));
  }

  /**
   * Handle security scan button click
   * @param {Event} event - Click event
   */
  handleScanClick(event) {
    const btn = event.currentTarget;
    const model = btn.dataset.model;
    const appNum = btn.dataset.appNum;
    
    if (!model || !appNum) {
      console.error('Missing required data attributes on security scan button');
      return;
    }
    
    // Store current analysis context
    this.dashboard.stateManager.currentAnalysis = { model, appNum };
    
    // Show modal
    document.getElementById('securityModal').classList.remove('hidden');
  }

  /**
   * Start security analysis
   */
  startAnalysis() {
    if (!this.dashboard.stateManager.currentAnalysis) return;
    
    const { model, appNum } = this.dashboard.stateManager.currentAnalysis;
    const analysisType = document.getElementById('analysisType').value || 'full';
    const aiModel = document.getElementById('aiModel').value || 'default';
    
    // Show loading state
    document.getElementById('scanResults').classList.add('hidden');
    document.getElementById('scanLoading').classList.remove('hidden');
    document.getElementById('startAnalysis').disabled = true;
    
    this.appendToLog(`Starting security analysis with type=${analysisType}, model=${aiModel}`);
    
    // Run analysis
    this.dashboard.apiService.post('/api/security/analyze-file', {
      model: model,
      app_num: appNum,
      analysis_type: analysisType,
      ai_model: aiModel
    }, {
      contentType: 'application/json'
    })
    .done(results => {
      // Update results display
      if (results) {
        document.getElementById('modalHighCount').textContent = results.counts?.high || 0;
        document.getElementById('modalMediumCount').textContent = results.counts?.medium || 0;
        document.getElementById('modalLowCount').textContent = results.counts?.low || 0;
        document.getElementById('summaryDetails').textContent = results.summary || 'No issues found';
        document.getElementById('aiAnalysis').textContent = results.ai_analysis || 'No analysis available';
        
        // Update app UI with results
        this.updateSecurityBadges(model, appNum, results);
      }
      
      // Show results
      document.getElementById('scanLoading').classList.add('hidden');
      document.getElementById('scanResults').classList.remove('hidden');
    })
    .fail(error => {
      this.dashboard.uiController.showToast(`Analysis failed: ${error.message || error}`, 'error');
      document.getElementById('scanLoading').classList.add('hidden');
      
      this.dashboard.errorHandler.handleError(
        error,
        { 
          action: 'securityAnalysis', 
          model, 
          appNum, 
          analysisType, 
          aiModel 
        }
      );
    })
    .always(() => {
      document.getElementById('startAnalysis').disabled = false;
    });
  }

  /**
   * Update security badges with analysis results
   * @param {string} model - Model name
   * @param {string|number} appNum - App number
   * @param {Object} results - Analysis results
   */
  updateSecurityBadges(model, appNum, results) {
    const appCard = document.querySelector(`[data-model="${model}"][data-app-id="${appNum}"]`);
    if (!appCard) return;
    
    const indicator = appCard.querySelector('.security-indicator');
    if (!indicator) return;
    
    if (results.total_issues > 0) {
      // Determine severity level
      const securityLevel = results.counts.high > 0 ? 'high' :
                          results.counts.medium > 0 ? 'medium' : 'low';
      
      // Update indicator
      indicator.classList.remove('hidden');
      indicator.className = `security-indicator text-xs px-1 rounded ${
        securityLevel === 'high' ? 'bg-red-100 text-red-800' :
        securityLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' :
        'bg-blue-100 text-blue-800'
      }`;
      
      indicator.textContent = `${results.total_issues} ${
        securityLevel === 'high' ? 'High' :
        securityLevel === 'medium' ? 'Med' : 'Low'
      }`;
    } else {
      indicator.classList.add('hidden');
    }
  }

  /**
   * Load security summary from API
   */
  loadSecuritySummary() {
    this.dashboard.apiService.get('/api/security/global-summary')
      .done(data => {
        // Update global counters
        this.dashboard.uiService.updateElement('#totalHighIssues', data.totals?.high || 0);
        this.dashboard.uiService.updateElement('#totalMediumIssues', data.totals?.medium || 0);
        this.dashboard.uiService.updateElement('#totalLowIssues', data.totals?.low || 0);
        this.dashboard.uiService.updateElement(
          '#lastGlobalScan', 
          data.last_scan ? new Date(data.last_scan).toLocaleString() : 'Never'
        );
      })
      .fail(error => {
        console.error('Failed to load security summary:', error);
      });
  }
  
  /**
   * Append message to log
   * @param {string} message - Message to append
   */
  appendToLog(message) {
    const logElement = document.getElementById('securityLog');
    if (!logElement) return;
    
    const timestamp = new Date().toLocaleTimeString();
    logElement.textContent += `[${timestamp}] ${message}\n`;
    logElement.scrollTop = logElement.scrollHeight;
  }
}

/**
 * Performance Test Feature Class
 * Handles performance testing functionality
 */
class PerformanceTest {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }

  /**
   * Initialize performance test functionality
   */
  init() {
    this.setupEventListeners();
  }

  /**
   * Set up event listeners for performance testing
   */
  setupEventListeners() {
    this.dashboard.eventManager.on(document, 'click', '#runTest', this.runTest.bind(this));
    this.dashboard.eventManager.on(document, 'click', '#stopTest', this.stopTest.bind(this));
    this.dashboard.eventManager.on(document, 'click', '#clearLog', () => {
      document.getElementById('outputLog').textContent = '';
    });
  }

  /**
   * Run performance test
   */
  runTest() {
    const numUsers = parseInt(document.getElementById('numUsers').value) || 10;
    const duration = parseInt(document.getElementById('duration').value) || 30;
    const spawnRate = parseInt(document.getElementById('spawnRate').value) || 1;
    
    // Update UI for test start
    document.getElementById('runTest').disabled = true;
    document.getElementById('stopTest').classList.remove('hidden');
    document.getElementById('testStatus').textContent = 'Running...';
    document.getElementById('scanProgress').classList.remove('hidden');
    
    this.appendToLog(`Starting performance test with ${numUsers} users, ${duration}s duration, and ${spawnRate} spawn rate`);
    
    // Start progress simulation
    this.simulateProgress(duration);
    
    // Make API request
    this.dashboard.apiService.post(window.location.href, {
      num_users: numUsers,
      duration: duration,
      spawn_rate: spawnRate,
      endpoints: ["/", "/api/status"]
    }, {
      contentType: 'application/json'
    })
    .done(result => {
      if (result.status === 'success') {
        // Update progress to 100%
        document.getElementById('progressBar').style.width = '100%';
        
        // Update results display
        this.updateStatistics(result.data);
        this.appendToLog('Test completed successfully');
        
        // Show download button if report available
        if (result.report_path) {
          document.getElementById('downloadReport').classList.remove('hidden');
        }
      } else {
        throw new Error(result.error || 'Test failed');
      }
    })
    .fail(error => {
      document.getElementById('progressBar').style.width = '0%';
      document.getElementById('testStatus').textContent = 'Failed';
      this.appendToLog(`Error: ${error.message || 'Test failed'}`);
      this.dashboard.uiController.showToast(`Test failed: ${error.message || 'Unknown error'}`, 'error');
    })
    .always(() => {
      document.getElementById('runTest').disabled = false;
      document.getElementById('stopTest').classList.add('hidden');
    });
  }

  /**
   * Stop performance test
   */
  stopTest() {
    this.appendToLog('Stopping test...');
    
    this.dashboard.apiService.post(`${window.location.href}/stop`)
      .done(() => {
        this.appendToLog('Test stopped successfully');
        document.getElementById('testStatus').textContent = 'Stopped';
      })
      .fail(error => {
        this.appendToLog(`Failed to stop test: ${error.message || 'Unknown error'}`);
      })
      .always(() => {
        document.getElementById('runTest').disabled = false;
        document.getElementById('stopTest').classList.add('hidden');
      });
  }

  /**
   * Simulate progress for a test
   * @param {number} duration - Test duration in seconds
   */
  simulateProgress(duration) {
    let elapsed = 0;
    const interval = 1000; // Update every second
    const progressBar = document.getElementById('progressBar');
    
    if (!progressBar) return;
    
    progressBar.style.width = '0%';
    
    const timer = setInterval(() => {
      elapsed += interval;
      const percentage = Math.min(Math.floor((elapsed / (duration * 1000)) * 100), 95);
      progressBar.style.width = `${percentage}%`;
      
      if (elapsed >= duration * 1000) {
        clearInterval(timer);
      }
    }, interval);
  }

  /**
   * Update statistics with test results
   * @param {Object} data - Test result data
   */
  updateStatistics(data) {
    if (!data) return;
    
    // Update basic statistics
    const elementsToUpdate = {
      'totalRequests': data.total_requests || 0,
      'totalFailures': data.total_failures || 0,
      'requestsPerSec': data.requests_per_sec ? data.requests_per_sec.toFixed(2) : 0,
      'avgResponseTime': data.avg_response_time ? data.avg_response_time.toFixed(2) + ' ms' : '-',
      'medianResponseTime': data.median_response_time ? data.median_response_time.toFixed(2) + ' ms' : '-',
      'percentile95': data.percentile_95 ? data.percentile_95.toFixed(2) + ' ms' : '-',
      'percentile99': data.percentile_99 ? data.percentile_99.toFixed(2) + ' ms' : '-',
      'lastRun': data.start_time || 'Never',
      'testStatus': 'Completed'
    };
    
    Object.entries(elementsToUpdate).forEach(([id, value]) => {
      this.dashboard.uiService.updateElement(`#${id}`, value);
    });
    
    // Update endpoint table
    this.updateEndpointTable(data.endpoints || []);
    
    // Update error table
    this.updateErrorTable(data.errors || []);
    
    // Show/hide visualization
    this.dashboard.uiService.toggleVisibility(
      '#visualizationSection',
      data.endpoints && data.endpoints.length > 0
    );
  }

  /**
   * Update endpoint table with test results
   * @param {Array} endpoints - Endpoint data
   */
  updateEndpointTable(endpoints) {
    const tableBody = document.getElementById('endpointTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    if (endpoints && endpoints.length > 0) {
      endpoints.forEach(endpoint => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td class="border border-gray-300 px-2 py-1 text-xs">${endpoint.name || ''}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs">${endpoint.method || ''}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${endpoint.num_requests || 0}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${endpoint.num_failures || 0}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.median_response_time || 0).toFixed(2)}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.avg_response_time || 0).toFixed(2)}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.min_response_time || 0).toFixed(2)}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.max_response_time || 0).toFixed(2)}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.current_rps || 0).toFixed(2)}</td>
        `;
        tableBody.appendChild(row);
      });
    } else {
      const row = document.createElement('tr');
      row.innerHTML = `<td colspan="9" class="border border-gray-300 px-2 py-1 text-xs text-center">No endpoint data available</td>`;
      tableBody.appendChild(row);
    }
  }

  /**
   * Update error table with test results
   * @param {Array} errors - Error data
   */
  updateErrorTable(errors) {
    const errorSection = document.getElementById('errorSection');
    const errorTable = document.getElementById('errorTableBody');
    
    if (!errorSection || !errorTable) return;
    
    errorTable.innerHTML = '';
    
    if (errors && errors.length > 0) {
      errorSection.classList.remove('hidden');
      
      errors.forEach(error => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td class="border border-gray-300 px-2 py-1 text-xs text-red-600">${error.error_type || 'Unknown'}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs text-right">${error.count || 0}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs">${error.endpoint || ''}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs">${error.method || ''}</td>
          <td class="border border-gray-300 px-2 py-1 text-xs">${error.description || ''}</td>
        `;
        errorTable.appendChild(row);
      });
    } else {
      errorSection.classList.add('hidden');
    }
  }

  /**
   * Append message to log output
   * @param {string} message - Message to append
   */
  appendToLog(message) {
    const outputLog = document.getElementById('outputLog');
    if (!outputLog) return;
    
    const timestamp = new Date().toLocaleTimeString();
    outputLog.textContent += `[${timestamp}] ${message}\n`;
    outputLog.scrollTop = outputLog.scrollHeight;
  }
}

/**
 * Requirements Analysis Feature Class
 * Handles requirements analysis functionality
 */
class RequirementsAnalysis {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }

  /**
   * Initialize requirements analysis functionality
   */
  init() {
    this.setupEventListeners();
    this.setupForm();
  }

  /**
   * Set up event listeners for requirements analysis
   */
  setupEventListeners() {
    // Toggle requirement details
    this.dashboard.eventManager.on(document, 'click', '.hover\\:bg-gray-50', e => {
      const detailId = $(e.currentTarget).attr('onclick')?.match(/toggleDetails\('([^']+)'\)/)?.[1];
      if (detailId) {
        $(`#${detailId}`).toggle();
      }
    });
  }

  /**
   * Set up form submission behavior
   */
  setupForm() {
    const $form = $('form');
    const $submitBtn = $('#submitBtn');
    
    if ($form.length && $submitBtn.length) {
      $form.on('submit', () => {
        $submitBtn.html(this.dashboard.uiService.getLoadingIndicator('Check'));
        $submitBtn.prop('disabled', true);
      });
    }
  }
}

/**
 * Security Analysis Page Feature Class
 * Handles security analysis page functionality
 */
class SecurityAnalysisPage {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
  }

  /**
   * Initialize security analysis page functionality
   */
  init() {
    this.setupFilters();
    this.setupExpandButtons();
  }

  /**
   * Set up filter functionality
   */
  setupFilters() {
    const $searchInput = $('#searchIssues');
    const $riskFilter = $('#riskFilter');
    const $confidenceFilter = $('#confidenceFilter');
    
    const applyFilters = () => {
      const searchTerm = $searchInput.val()?.toLowerCase() || '';
      const selectedRisk = $riskFilter.val() || 'all';
      const selectedConfidence = $confidenceFilter.val() || 'all';
      
      $('.alert-item').each(function() {
        const $alert = $(this);
        const risk = $alert.data('risk');
        const confidence = $alert.data('confidence');
        const searchText = $alert.data('searchable')?.toLowerCase() || '';
        
        const riskMatch = selectedRisk === 'all' || risk === selectedRisk;
        const confidenceMatch = selectedConfidence === 'all' || confidence === selectedConfidence;
        const searchMatch = !searchTerm || searchText.includes(searchTerm);
        
        $alert.toggle(riskMatch && confidenceMatch && searchMatch);
      });
    };
    
    // Add event listeners
    if ($searchInput.length) {
      $searchInput.on('input', this.dashboard.utilityService.debounce(applyFilters, 300));
    }
    
    if ($riskFilter.length) {
      $riskFilter.on('change', applyFilters);
    }
    
    if ($confidenceFilter.length) {
      $confidenceFilter.on('change', applyFilters);
    }
    
    // Initial filter application
    applyFilters();
  }

  /**
   * Set up expand buttons for alerts
   */
  setupExpandButtons() {
    this.dashboard.eventManager.on(document, 'click', '.expand-btn', e => {
      const $details = $(e.currentTarget).closest('div').next().find('.alert-details');
      $details.toggleClass('hidden');
      $(e.currentTarget).text($details.hasClass('hidden') ? 'Expand' : 'Collapse');
    });
  }
}

/**
 * ZAP Scan Feature Class
 * Handles ZAP scanning functionality
 */
class ZapScan {
  /**
   * @param {Dashboard} dashboard - Dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    this.scanPollId = null;
  }

  /**
   * Initialize ZAP scan functionality
   */
  init() {
    this.setupEventListeners();
    this.updateTargetUrl();
  }

  /**
   * Set up event listeners for ZAP scan
   */
  setupEventListeners() {
    this.setupScanButtons();
    this.setupExpandButtons();
  }

  /**
   * Set up scan control buttons
   */
  setupScanButtons() {
    this.dashboard.eventManager.on(document, 'click', '#startScan', this.startScan.bind(this));
    this.dashboard.eventManager.on(document, 'click', '#stopScan', this.stopScan.bind(this));
    this.dashboard.eventManager.on(document, 'click', '#clearLog', () => {
      document.getElementById('progressLog').textContent = '';
    });
  }

  /**
   * Set up expand buttons for scan results
   */
  setupExpandButtons() {
    this.dashboard.eventManager.on(document, 'click', '.expand-btn', e => {
      // Find the details container within the alert item
      const alertItem = e.currentTarget.closest('.alert-item');
      if (!alertItem) return;