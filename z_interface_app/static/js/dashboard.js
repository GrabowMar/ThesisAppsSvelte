/**
 * AI Model Management Dashboard
 * Main controller for dashboard functionality
 */
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = new DashboardController();
  window.dashboardInstance = dashboard; // Store globally for error handling
  dashboard.init();
  setupErrorHandling();
});

/**
 * Set up global error handlers and request interceptors
 */
function setupErrorHandling() {
  // Global error handler for uncaught exceptions
  window.addEventListener('error', function(event) {
    const errorDetails = {
      message: event.message,
      filename: event.filename, 
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error ? event.error.stack : 'No stack trace',
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };
    
    console.error('CLIENT ERROR:', errorDetails);
    
    // Send error to server for logging
    fetch('/api/log-client-error', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(errorDetails)
    }).catch(err => {
      console.error('Failed to send error to server:', err);
    });
  });
  
  // Intercept fetch requests to prevent malformed URLs
  const originalFetch = window.fetch;
  window.fetch = function(url, options) {
    // Check for malformed URLs
    if (typeof url === 'string' && url.includes('/undefined')) {
      const error = new Error(`Prevented malformed request to ${url}`);
      console.error('FETCH ERROR:', error);
      
      // Log the error
      if (window.dashboardInstance && window.dashboardInstance.logClientError) {
        window.dashboardInstance.logClientError({
          message: 'Prevented malformed fetch request',
          url: url,
          stack: error.stack,
          type: 'MALFORMED_URL'
        });
      }
      
      // Return a rejected promise instead of making the bad request
      return Promise.reject(error);
    }
    
    // Log all fetch requests in development
    console.log(`FETCH REQUEST: ${url}`, options);
    
    // Proceed with the original fetch for valid URLs
    return originalFetch(url, options)
      .then(response => {
        if (!response.ok) {
          console.warn(`FETCH ERROR: ${response.status} for ${url}`);
        }
        return response;
      })
      .catch(error => {
        console.error(`FETCH FAILURE: ${url}`, error);
        throw error;
      });
  };
}

/**
 * Main Dashboard Controller class
 */
class DashboardController {
  constructor() {
    // Configuration
    this.config = {
      autoRefreshInterval: null,
      autoRefreshDuration: 30000, // 30 seconds
      maxRetries: 3,
      retryDelay: 1000,
      toastDuration: 3000
    };
    
    // Element selectors - centralize for easier maintenance
    this.selectors = {
      actionButtons: '.action-btn',
      refreshAll: '#refreshAll',
      toggleAutorefresh: '#toggleAutorefresh',
      autorefreshText: '#autorefreshText',
      quickActions: '[data-quick-action]',
      appCards: '[data-app-id]',
      searchApps: '#searchApps',
      filterModel: '#filterModel',
      filterStatus: '#filterStatus',
      healthStatus: '[data-health-status]',
      dockerStatus: '[data-docker-status]',
      lastUpdate: '[data-last-update]',
      noResultsMessage: '#noResultsMessage',
      modelSections: '[data-model-section]'
    };
    
    // State tracking
    this.state = {
      isRefreshing: false,
      lastRefreshTime: null,
      pendingActions: new Map()
    };
  }

  /**
   * Initialize the dashboard
   */
  init() {
    try {
      this.initializeEventListeners();
      this.setupAutoRefresh();
      this.setupFilters();
      this.updateSystemInfo();
      this.logInitialization();
    } catch (error) {
      console.error('Dashboard initialization failed:', error);
      this.showToast('Dashboard initialization failed. Please refresh the page.', 'error');
      this.logClientError({
        message: 'Dashboard initialization failed',
        error: error.toString(),
        stack: error.stack,
        type: 'INITIALIZATION_ERROR'
      });
    }
  }

  /**
   * Set up all event listeners
   */
  initializeEventListeners() {
    // Action buttons (start, stop, reload, etc.)
    document.querySelectorAll(this.selectors.actionButtons).forEach(button => {
      button.addEventListener('click', this.handleAction.bind(this));
    });

    // Global refresh button
    const refreshBtn = document.querySelector(this.selectors.refreshAll);
    if (refreshBtn) {
      refreshBtn.addEventListener('click', this.refreshAllStatuses.bind(this));
    }

    // Auto-refresh toggle
    const autoRefreshBtn = document.querySelector(this.selectors.toggleAutorefresh);
    if (autoRefreshBtn) {
      autoRefreshBtn.addEventListener('click', this.toggleAutoRefresh.bind(this));
    }

    // Quick action buttons
    document.querySelectorAll(this.selectors.quickActions).forEach(button => {
      button.addEventListener('click', this.handleQuickAction.bind(this));
    }); 

    // Add visibility change handler to pause auto-refresh when tab is inactive
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
  }

  /**
   * Handle visibility change to save resources when tab is inactive
   */
  handleVisibilityChange() {
    if (document.hidden) {
      this.pauseAutoRefresh();
    } else {
      this.resumeAutoRefresh();
    }
  }

  /**
   * Set up auto-refresh functionality
   */
  setupAutoRefresh() {
    const toggle = document.querySelector(this.selectors.toggleAutorefresh);
    if (!toggle) return;

    // Check if auto-refresh is enabled in localStorage
    const isEnabled = localStorage.getItem('autoRefreshEnabled') === 'true';
    
    if (isEnabled) {
      this.startAutoRefresh();
      toggle.textContent = 'Disable Auto-Refresh';
    } else {
      toggle.textContent = 'Enable Auto-Refresh';
    }
  }

  /**
   * Toggle auto-refresh on/off
   */
  toggleAutoRefresh() {
    const toggle = document.querySelector(this.selectors.toggleAutorefresh);
    if (!toggle) return;

    const isCurrentlyEnabled = !!this.config.autoRefreshInterval;
    
    if (isCurrentlyEnabled) {
      this.stopAutoRefresh();
      toggle.textContent = 'Enable Auto-Refresh';
      localStorage.setItem('autoRefreshEnabled', 'false');
    } else {
      this.startAutoRefresh();
      toggle.textContent = 'Disable Auto-Refresh';
      localStorage.setItem('autoRefreshEnabled', 'true');
    }
  }

  /**
   * Start auto-refresh timer
   */
  startAutoRefresh() {
    if (this.config.autoRefreshInterval) return;
    
    console.log(`Starting auto-refresh every ${this.config.autoRefreshDuration/1000} seconds`);
    this.config.autoRefreshInterval = setInterval(() => {
      this.refreshAllStatuses();
    }, this.config.autoRefreshDuration);
    
    const statusText = document.querySelector(this.selectors.autorefreshText);
    if (statusText) {
      statusText.textContent = `Auto-refreshing every ${this.config.autoRefreshDuration/1000}s`;
      statusText.classList.remove('hidden');
    }
  }

  /**
   * Stop auto-refresh timer
   */
  stopAutoRefresh() {
    if (this.config.autoRefreshInterval) {
      clearInterval(this.config.autoRefreshInterval);
      this.config.autoRefreshInterval = null;
      
      const statusText = document.querySelector(this.selectors.autorefreshText);
      if (statusText) {
        statusText.textContent = 'Auto-refresh disabled';
      }
    }
  }

  /**
   * Pause auto-refresh (for tab inactivity)
   */
  pauseAutoRefresh() {
    if (this.config.autoRefreshInterval) {
      console.log('Pausing auto-refresh (tab inactive)');
      clearInterval(this.config.autoRefreshInterval);
      this.config.autoRefreshInterval = null;
      this.state.autoRefreshPaused = true;
    }
  }

  /**
   * Resume auto-refresh after pause
   */
  resumeAutoRefresh() {
    if (this.state.autoRefreshPaused && localStorage.getItem('autoRefreshEnabled') === 'true') {
      console.log('Resuming auto-refresh (tab active)');
      this.startAutoRefresh();
      this.state.autoRefreshPaused = false;
    }
  }

  /**
   * Set up search and filter functionality
   */
  setupFilters() {
    const searchInput = document.querySelector(this.selectors.searchApps);
    const modelFilter = document.querySelector(this.selectors.filterModel);
    const statusFilter = document.querySelector(this.selectors.filterStatus);
    
    if (searchInput) {
      searchInput.addEventListener('input', this.debounce(() => {
        this.filterApps();
      }, 300));
    }
    
    if (modelFilter) {
      modelFilter.addEventListener('change', () => {
        this.filterApps();
      });
    }
    
    if (statusFilter) {
      statusFilter.addEventListener('change', () => {
        this.filterApps();
      });
    }
  }

  /**
   * Filter application cards based on search/filter criteria
   */
  filterApps() {
    const searchInput = document.querySelector(this.selectors.searchApps);
    const modelFilter = document.querySelector(this.selectors.filterModel);
    const statusFilter = document.querySelector(this.selectors.filterStatus);
    
    if (!searchInput && !modelFilter && !statusFilter) return;
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const modelValue = modelFilter ? modelFilter.value : 'all';
    const statusValue = statusFilter ? statusFilter.value : 'all';
    
    document.querySelectorAll(this.selectors.appCards).forEach(card => {
      const model = card.dataset.model || '';
      const appName = card.dataset.appName || '';
      const appId = card.dataset.appId || '';
      const status = card.dataset.status || '';
      
      const matchesSearch = !searchTerm || 
                            appName.toLowerCase().includes(searchTerm) || 
                            appId.includes(searchTerm);
      const matchesModel = modelValue === 'all' || model === modelValue;
      const matchesStatus = statusValue === 'all' || status === statusValue;
      
      const isVisible = matchesSearch && matchesModel && matchesStatus;
      card.style.display = isVisible ? '' : 'none';
    });
    
    this.toggleNoResultsMessage();
  }

  /**
   * Toggle the "no results" message based on filter results
   */
  toggleNoResultsMessage() {
    const noResults = document.querySelector(this.selectors.noResultsMessage);
    if (!noResults) return;
    
    const hasAnyVisible = document.querySelector(`${this.selectors.appCards}:not([style*="display: none"])`);
    noResults.classList.toggle('hidden', !!hasAnyVisible);
  }

  /**
   * Handle action button clicks (start, stop, reload, etc.)
   * @param {Event} event - Click event
   */
  async handleAction(event) {
    const button = event.currentTarget;
    if (!button || !button.dataset) {
      console.error('Invalid action button:', button);
      return;
    }

    const { action, model, appNum } = button.dataset;
    
    // Validate required data attributes
    if (!action || !model || !appNum) {
      const errorMsg = 'Missing required data attributes on button';
      console.error(errorMsg, { button, dataset: button.dataset });
      this.showToast('Operation failed: Button misconfiguration', 'error');
      this.logClientError({
        message: errorMsg,
        type: 'BUTTON_CONFIGURATION_ERROR',
        element: button.outerHTML,
        dataset: { ...button.dataset }
      });
      return;
    }
    
    // Prevent duplicate actions
    const actionKey = `${action}-${model}-${appNum}`;
    if (this.state.pendingActions.has(actionKey)) {
      console.log(`Action ${actionKey} already in progress, skipping`);
      return;
    }

    const originalText = button.textContent;
    this.state.pendingActions.set(actionKey, true);

    try {
      button.disabled = true;
      button.innerHTML = this.getLoadingSpinner(action);

      // Execute action with retry logic
      const success = await this.executeWithRetry(
        () => this.performAction(action, model, appNum),
        this.config.maxRetries
      );

      if (success) {
        await this.updateAppStatus(model, appNum);
        this.showToast(`${this.capitalizeFirst(action)} completed successfully`);
      } else {
        throw new Error(`Failed to ${action} after multiple attempts`);
      }
    } catch (error) {
      console.error(`Action '${action}' failed:`, error);
      this.showToast(error.message || `Failed to ${action}`, 'error');
      this.logClientError({
        message: `Action '${action}' failed: ${error.message}`,
        type: 'ACTION_FAILURE',
        context: { action, model, appNum },
        stack: error.stack
      });
    } finally {
      button.disabled = false;
      button.textContent = originalText;
      this.state.pendingActions.delete(actionKey);
    }
  }

  /**
   * Get HTML for loading spinner
   * @param {string} action - Current action
   * @returns {string} - HTML for spinner
   */
  getLoadingSpinner(action) {
    return `<span class="spinner inline-block w-4 h-4 border-2 border-t-blue-500 border-r-transparent border-b-blue-500 border-l-transparent rounded-full animate-spin mr-1"></span> ${this.capitalizeFirst(action)}ing...`;
  }

  /**
   * Perform an action via API
   * @param {string} action - The action to perform
   * @param {string} model - The model name
   * @param {string} appNum - The app number
   * @returns {Promise<boolean>} - Success status
   */
  async performAction(action, model, appNum) {
    // Parameter validation
    if (!action || !model || !appNum) {
      const errorMsg = `Invalid request parameters: action=${action}, model=${model}, appNum=${appNum}`;
      console.error(errorMsg);
      this.logClientError({
        message: errorMsg,
        type: 'REQUEST_PARAMETER_ERROR',
        context: { action, model, appNum }
      });
      throw new Error('Missing required parameters for this operation');
    }
    
    try {
      // Show special handling for rebuild which may take longer
      if (action === 'rebuild') {
        this.showToast(`Rebuilding ${model} App ${appNum}. This may take several minutes...`, 'info');
      }
      
      const response = await fetch(`/${action}/${model}/${appNum}`, {
        headers: { 
          'X-Requested-With': 'XMLHttpRequest',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        let errorMsg = `Action failed: ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          if (errorData && errorData.message) {
            errorMsg = errorData.message;
          }
        } catch (e) {
          // Response might not be JSON, that's OK
        }
        
        console.error(`Error during ${action}:`, errorMsg);
        throw new Error(errorMsg);
      }
      
      try {
        const data = await response.json();
        // If we received a more detailed message, show it
        if (data && data.message) {
          console.log(`${action} response:`, data.message);
        }
      } catch (e) {
        // Response might not be JSON, that's OK
      }
      
      return true;
    } catch (error) {
      console.error(`Error during ${action}:`, error);
      throw error;
    }
  }

  /**
   * Update app status after an action
   * @param {string} model - The model name 
   * @param {string} appNum - The app number
   */
  async updateAppStatus(model, appNum) {
    // Validate parameters
    if (!model || !appNum) {
      console.warn('Skipping status update due to missing parameters', { model, appNum });
      return;
    }
    
    try {
      const response = await fetch(`/status/${model}/${appNum}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get status: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.updateStatusDisplay(model, appNum, data);
    } catch (error) {
      console.error(`Error updating status for ${model} app ${appNum}:`, error);
      this.logClientError({
        message: `Failed to update status for ${model}/${appNum}`,
        type: 'STATUS_UPDATE_ERROR',
        error: error.toString(),
        stack: error.stack
      });
    }
  }

  /**
   * Update status display with new data
   * @param {string} model - Model name
   * @param {string} appNum - App number
   * @param {Object} data - Status data
   */
  updateStatusDisplay(model, appNum, data) {
    if (!model || !appNum || !data) {
      console.warn('Cannot update status display with invalid parameters');
      return;
    }
    
    const appCard = document.querySelector(`[data-model="${model}"][data-app-id="${appNum}"]`);
    if (!appCard) {
      console.warn(`App card not found for ${model}/${appNum}`);
      return;
    }
    
    try {
      // Update Docker status
      const dockerStatus = appCard.querySelector(this.selectors.dockerStatus);
      if (dockerStatus) {
        dockerStatus.textContent = data.docker_status || 'Unknown';
        dockerStatus.className = this.getStatusClass(data.docker_status);
      }
      
      // Update health status
      const healthStatus = appCard.querySelector(this.selectors.healthStatus);
      if (healthStatus) {
        healthStatus.textContent = data.health_status || 'Unknown';
        healthStatus.className = this.getHealthClass(data, data.health_status);
      }
      
      // Update last checked time
      const lastUpdate = appCard.querySelector(this.selectors.lastUpdate);
      if (lastUpdate) {
        const now = new Date();
        lastUpdate.textContent = `Last checked: ${now.toLocaleTimeString()}`;
      }
      
      // Update app card status attribute for filtering
      appCard.dataset.status = data.docker_status || 'unknown';
      
      // Update additional metrics if available
      if (data.metrics) {
        this.updateMetricsDisplay(appCard, data.metrics);
      }
    } catch (error) {
      console.error('Error updating status display:', error);
    }
  }

  /**
   * Update metrics display if available
   * @param {Element} card - App card element
   * @param {Object} metrics - Metrics data
   */
  updateMetricsDisplay(card, metrics) {
    if (!card || !metrics) return;
    
    // CPU usage
    const cpuElement = card.querySelector('.metric-cpu');
    if (cpuElement && metrics.cpu_percent) {
      cpuElement.textContent = `${metrics.cpu_percent.toFixed(1)}%`;
    }
    
    // Memory usage
    const memElement = card.querySelector('.metric-memory');
    if (memElement && metrics.memory_usage) {
      memElement.textContent = this.formatBytes(metrics.memory_usage);
    }
    
    // Request count
    const requestsElement = card.querySelector('.metric-requests');
    if (requestsElement && metrics.request_count !== undefined) {
      requestsElement.textContent = metrics.request_count.toLocaleString();
    }
  }

  /**
   * Format bytes to human-readable format
   * @param {number} bytes - Bytes to format
   * @returns {string} - Formatted string
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get CSS class for Docker status
   * @param {string} status - Docker status
   * @returns {string} - CSS class
   */
  getStatusClass(status) {
    if (!status) return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    
    switch (status.toLowerCase()) {
      case 'running':
        return 'px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded';
      case 'stopped':
      case 'exited':
        return 'px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded';
      case 'restarting':
        return 'px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded';
      default:
        return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    }
  }

  /**
   * Get CSS class for health status
   * @param {Object} data - Full status data
   * @param {string} status - Health status
   * @returns {string} - CSS class
   */
  getHealthClass(data, status) {
    if (!status) return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    
    // If docker is not running, health is irrelevant
    if (data.docker_status && 
        ['stopped', 'exited'].includes(data.docker_status.toLowerCase())) {
      return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    }
    
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded';
      case 'unhealthy':
        return 'px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded';
      case 'starting':
        return 'px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded';
      default:
        return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    }
  }

  /**
   * Handle quick actions (system-wide operations)
   * @param {Event} event - Click event
   */
  async handleQuickAction(event) {
    const button = event.currentTarget;
    const { quickAction } = button.dataset;
    
    if (!quickAction) {
      console.error('Quick action button missing data-quick-action attribute');
      return;
    }
    
    // Confirm potentially destructive actions
    if (['restart-all', 'stop-all', 'update-all'].includes(quickAction)) {
      if (!confirm(`Are you sure you want to ${quickAction.replace('-all', ' all apps')}?`)) {
        return;
      }
    }
    
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = this.getLoadingSpinner(quickAction.replace('-all', ''));
    
    try {
      const response = await fetch(`/api/${quickAction}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Action failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      this.showToast(data.message || 'Operation completed successfully');
      
      // Refresh statuses after global operation
      setTimeout(() => {
        this.refreshAllStatuses();
      }, 1000);
    } catch (error) {
      console.error(`Quick action '${quickAction}' failed:`, error);
      this.showToast(error.message || 'Operation failed', 'error');
      this.logClientError({
        message: `Quick action '${quickAction}' failed: ${error.message}`,
        type: 'QUICK_ACTION_ERROR',
        stack: error.stack
      });
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  }

  /**
   * Refresh all app statuses
   */
  async refreshAllStatuses() {
    if (this.state.isRefreshing) return;
    
    this.state.isRefreshing = true;
    console.log('Refreshing all app statuses...');
    
    try {
      // Get all model sections with proper validation
      document.querySelectorAll(this.selectors.modelSections).forEach(async (modelSection) => {
        const model = modelSection.dataset.modelSection;
        if (!model) {
          console.warn('Model section missing data-model-section attribute', modelSection);
          return;
        }
        
        const appCards = modelSection.querySelectorAll(`[data-model="${model}"][data-app-id]`);
        console.log(`Refreshing ${appCards.length} apps for model ${model}`);
        
        for (const card of appCards) {
          const appNum = card.dataset.appId;
          if (!appNum) {
            console.warn('App card missing data-app-id attribute', card);
            continue;
          }
          
          try {
            await this.updateAppStatus(model, appNum);
          } catch (error) {
            console.error(`Error refreshing status for ${model} app ${appNum}:`, error);
          }
        }
      });
      
      // Update refresh timestamp
      this.state.lastRefreshTime = new Date();
      this.updateRefreshTimestamp();
    } catch (error) {
      console.error('Error in refresh all:', error);
      this.logClientError({
        message: 'Failed to refresh all statuses',
        error: error.toString(),
        stack: error.stack,
        type: 'REFRESH_ERROR'
      });
    } finally {
      this.state.isRefreshing = false;
    }
  }

  /**
   * Update system info display
   */
  async updateSystemInfo() {
    try {
      const response = await fetch('/api/system-info', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch system info');
      }
      
      const data = await response.json();
      this.updateSystemInfoDisplay(data);
    } catch (error) {
      console.error('Failed to update system info:', error);
    }
  }

  /**
   * Update the system info display elements
   * @param {Object} data - System info data
   */
  updateSystemInfoDisplay(data) {
    if (!data) return;
    
    // Update CPU usage
    const cpuElement = document.getElementById('systemCpuUsage');
    if (cpuElement && data.cpu_percent !== undefined) {
      cpuElement.textContent = `${data.cpu_percent.toFixed(1)}%`;
      
      // Add color classes based on thresholds
      cpuElement.className = data.cpu_percent > 80 
        ? 'text-red-600 font-medium' 
        : data.cpu_percent > 50 
          ? 'text-yellow-600 font-medium' 
          : 'text-green-600 font-medium';
    }
    
    // Update Memory usage
    const memElement = document.getElementById('systemMemoryUsage');
    if (memElement && data.memory_percent !== undefined) {
      memElement.textContent = `${data.memory_percent.toFixed(1)}%`;
      
      // Add color classes based on thresholds
      memElement.className = data.memory_percent > 85 
        ? 'text-red-600 font-medium' 
        : data.memory_percent > 70 
          ? 'text-yellow-600 font-medium' 
          : 'text-green-600 font-medium';
    }
    
    // Update Disk usage
    const diskElement = document.getElementById('systemDiskUsage');
    if (diskElement && data.disk_percent !== undefined) {
      diskElement.textContent = `${data.disk_percent.toFixed(1)}%`;
      
      // Add color classes based on thresholds
      diskElement.className = data.disk_percent > 90 
        ? 'text-red-600 font-medium' 
        : data.disk_percent > 75 
          ? 'text-yellow-600 font-medium' 
          : 'text-green-600 font-medium';
    }
    
    // Update uptime
    const uptimeElement = document.getElementById('systemUptime');
    if (uptimeElement && data.uptime_seconds !== undefined) {
      uptimeElement.textContent = this.formatUptime(data.uptime_seconds);
    }
  }

  /**
   * Format uptime in readable format
   * @param {number} seconds - Uptime in seconds
   * @returns {string} - Formatted uptime
   */
  formatUptime(seconds) {
    if (seconds === undefined) return 'Unknown';
    
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
   * Update the refresh timestamp display
   */
    updateRefreshTimestamp() {
      if (!this.state.lastRefreshTime) return;
      
      const refreshTimeEl = document.getElementById('lastRefreshTime');
      if (refreshTimeEl) {
        refreshTimeEl.textContent = this.state.lastRefreshTime.toLocaleTimeString();
      }
    }
  
    /**
     * Execute a function with retry logic
     * @param {Function} fn - Function to execute
     * @param {number} maxRetries - Maximum retry attempts
     * @returns {Promise<any>} - Result of function
     */
    async executeWithRetry(fn, maxRetries) {
      let lastError;
      
      for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
          return await fn();
        } catch (error) {
          console.warn(`Attempt ${attempt + 1}/${maxRetries} failed:`, error);
          lastError = error;
          
          // Wait before retry (exponential backoff)
          if (attempt < maxRetries - 1) {
            await new Promise(resolve => 
              setTimeout(resolve, this.config.retryDelay * Math.pow(2, attempt))
            );
          }
        }
      }
      
      throw lastError;
    }
  
    /**
     * Debounce a function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Debounce delay in ms
     * @returns {Function} - Debounced function
     */
    debounce(func, wait) {
      let timeout;
      return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
      };
    }
  
    /**
     * Capitalize first letter of a string
     * @param {string} str - Input string
     * @returns {string} - Capitalized string
     */
    capitalizeFirst(str) {
      if (!str) return '';
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
  
    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type (success, error, info)
     */
    showToast(message, type = 'success') {
      if (!message) return;
      
      // Create toast container if it doesn't exist
      let toastContainer = document.getElementById('toastContainer');
      if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(toastContainer);
      }
      
      // Create toast element
      const toast = document.createElement('div');
      toast.className = `px-4 py-2 rounded-sm shadow-md text-sm ${
        type === 'success' ? 'bg-green-100 border border-green-300 text-green-800' :
        type === 'error' ? 'bg-red-100 border border-red-300 text-red-800' :
        'bg-blue-100 border border-blue-300 text-blue-800'
      }`;
      toast.innerText = message;
      
      // Add to container
      toastContainer.appendChild(toast);
      
      // Remove after delay
      setTimeout(() => {
        toast.classList.add('opacity-0', 'transition-opacity', 'duration-500');
        setTimeout(() => {
          toast.remove();
          
          // Remove container if empty
          if (toastContainer.children.length === 0) {
            toastContainer.remove();
          }
        }, 500);
      }, this.config.toastDuration);
    }
  
    /**
     * Log client errors in a structured way
     * @param {Object} errorData - Error data to log
     */
    logClientError(errorData) {
      if (!errorData) return;
      
      const enhancedErrorData = {
        ...errorData,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      };
      
      console.error('CLIENT ERROR:', enhancedErrorData);
      
      // Send to server
      fetch('/api/log-client-error', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(enhancedErrorData)
      }).catch(err => {
        console.error('Failed to send error to server:', err);
      });
    }
  
    /**
     * Log initialization information
     */
    logInitialization() {
      console.log('AI Model Management Dashboard initialized');
      console.log('Auto-refresh interval:', this.config.autoRefreshDuration / 1000, 'seconds');
    }
  }
  
  /**
   * Batch operation handler
   * Handle bulk operations on multiple apps
   */
  function setupBatchOperations() {
    // Set up dropdown toggles for batch operation menus
    document.querySelectorAll('.batch-menu-button').forEach(button => {
      button.addEventListener('click', (e) => {
        e.stopPropagation();
        const dropdown = button.nextElementSibling;
        if (!dropdown) return;
        
        dropdown.classList.toggle('hidden');
        
        // Close other open dropdowns
        document.querySelectorAll('.batch-menu-items').forEach(menu => {
          if (menu !== dropdown && !menu.classList.contains('hidden')) {
            menu.classList.add('hidden');
          }
        });
      });
    });
    
    // Close dropdowns when clicking elsewhere
    document.addEventListener('click', () => {
      document.querySelectorAll('.batch-menu-items').forEach(menu => {
        menu.classList.add('hidden');
      });
    });
    
    // Handle batch action clicks
    document.querySelectorAll('.batch-action').forEach(button => {
      button.addEventListener('click', async function() {
        if (!this.dataset || !this.dataset.model || !this.dataset.action) {
          console.error('Batch action button missing required attributes');
          return;
        }
        
        const model = this.dataset.model;
        const action = this.dataset.action;
        const modelSection = document.querySelector(`[data-model-section="${model}"]`);
        
        if (!modelSection) {
          console.error(`Model section not found for model ${model}`);
          return;
        }
        
        // Get confirmation from user
        if (!confirm(`Are you sure you want to ${action} all apps for model ${model}?`)) {
          return;
        }
        
        // Find all apps for this model
        const appCards = modelSection.querySelectorAll(`[data-model="${model}"][data-app-id]`);
        if (appCards.length === 0) {
          showToast(`No apps found for model ${model}`);
          return;
        }
        
        // Show batch operation status
        const statusEl = modelSection.querySelector('.batch-status');
        if (!statusEl) {
          console.warn(`Status element not found for batch operation on model ${model}`);
          return;
        }
        
        const statusTextEl = statusEl.querySelector('.batch-status-text');
        const progressEl = statusEl.querySelector('.batch-progress');
        
        if (statusTextEl) statusTextEl.textContent = `${action.charAt(0).toUpperCase() + action.slice(1)}ing apps...`;
        if (progressEl) progressEl.textContent = `0/${appCards.length}`;
        statusEl.classList.remove('hidden');
        
        // Track success and failure counts
        let success = 0;
        let failed = 0;
        
        // Process apps in batches of 3 to avoid overloading the server
        const batchSize = 3;
        const appNumbers = Array.from(appCards).map(card => card.dataset.appId).filter(Boolean);
        
        for (let i = 0; i < appNumbers.length; i += batchSize) {
          const batch = appNumbers.slice(i, i + batchSize);
          
          // Start concurrent operations for this batch
          const batchPromises = batch.map(appNum => processBatchOperation(model, appNum, action));
          
          // Wait for all operations in this batch to complete
          const results = await Promise.allSettled(batchPromises);
          
          // Update counts based on results
          results.forEach(result => {
            if (result.status === 'fulfilled' && result.value === true) {
              success++;
            } else {
              failed++;
            }
          });
          
          // Update progress display
          if (progressEl) progressEl.textContent = `${success + failed}/${appNumbers.length}`;
        }
        
        // Update final status
        if (statusTextEl) {
          if (failed === 0) {
            statusTextEl.textContent = `All apps ${action}ed successfully`;
            if (statusEl.querySelector('span')) {
              statusEl.querySelector('span').className = 'px-2 py-0.5 text-xs bg-green-100 text-green-800 border border-green-300 rounded-sm';
            }
          } else if (success === 0) {
            statusTextEl.textContent = `Failed to ${action} all apps`;
            if (statusEl.querySelector('span')) {
              statusEl.querySelector('span').className = 'px-2 py-0.5 text-xs bg-red-100 text-red-800 border border-red-300 rounded-sm';
            }
          } else {
            statusTextEl.textContent = `${success} succeeded, ${failed} failed`;
            if (statusEl.querySelector('span')) {
              statusEl.querySelector('span').className = 'px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 border border-yellow-300 rounded-sm';
            }
          }
        }
        
        // Hide status after delay if successful, keep visible if there were failures
        if (failed === 0) {
          setTimeout(() => {
            statusEl.classList.add('hidden');
          }, 5000);
        }
        
        // Refresh app statuses after batch operation
        setTimeout(() => {
          if (window.dashboardInstance) {
            window.dashboardInstance.refreshAllStatuses();
          } else {
            refreshAppStatuses(model);
          }
        }, 1000);
      });
    });
  }
  
  /**
   * Process a single batch operation for an app
   * @param {string} model - Model name
   * @param {string} appNum - App number
   * @param {string} action - Action to perform (start, stop, reload, etc.)
   * @returns {Promise<boolean>} Success or failure
   */
  async function processBatchOperation(model, appNum, action) {
    // Parameter validation
    if (!model || !appNum || !action) {
      console.error('Invalid batch operation parameters', { model, appNum, action });
      return false;
    }
    
    try {
      // Handle special non-Docker actions
      if (action === 'health-check') {
        const response = await fetch(`/api/health/${model}/${appNum}`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) throw new Error(`Health check failed for app ${appNum}`);
        return true;
      }
      
      // Show special handling for rebuild which may take longer
      if (action === 'rebuild') {
        showToast(`Rebuilding ${model} App ${appNum}. This may take several minutes...`, 'info');
      }
      
      // Handle standard actions
      const response = await fetch(`/${action}/${model}/${appNum}`, {
        headers: { 
          'X-Requested-With': 'XMLHttpRequest',
          'Cache-Control': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to ${action} app ${appNum}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error processing ${action} for ${model} app ${appNum}:`, error);
      return false;
    }
  }
  
  /**
   * Refresh the status display for all apps of a model
   * @param {string} model - Model name
   */
  async function refreshAppStatuses(model) {
    if (!model) {
      console.error('Cannot refresh app statuses: model is undefined');
      return;
    }
    
    const modelSection = document.querySelector(`[data-model-section="${model}"]`);
    if (!modelSection) {
      console.error(`Model section not found for ${model}`);
      return;
    }
    
    const appCards = modelSection.querySelectorAll(`[data-model="${model}"][data-app-id]`);
    
    for (const card of appCards) {
      const appNum = card.dataset.appId;
      if (!appNum) {
        console.warn('App card missing data-app-id attribute', card);
        continue;
      }
      
      try {
        const response = await fetch(`/status/${model}/${appNum}`, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
          }
        });
        
        if (!response.ok) {
          console.error(`Failed to get status for ${model}/${appNum}: ${response.statusText}`);
          continue;
        }
        
        const data = await response.json();
        updateCardStatus(card, data);
      } catch (error) {
        console.error(`Error refreshing status for ${model} app ${appNum}:`, error);
      }
    }
  }
  
  /**
   * Update card status with new data
   * @param {Element} card - App card element
   * @param {Object} data - Status data
   */
  function updateCardStatus(card, data) {
    if (!card || !data) return;
    
    // Update Docker status
    const dockerStatus = card.querySelector('[data-docker-status]');
    if (dockerStatus) {
      dockerStatus.textContent = data.docker_status || 'Unknown';
      dockerStatus.className = getStatusClass(data.docker_status);
    }
    
    // Update health status
    const healthStatus = card.querySelector('[data-health-status]');
    if (healthStatus) {
      healthStatus.textContent = data.health_status || 'Unknown';
      healthStatus.className = getHealthClass(data, data.health_status);
    }
    
    // Update last checked time
    const lastUpdate = card.querySelector('[data-last-update]');
    if (lastUpdate) {
      const now = new Date();
      lastUpdate.textContent = `Last checked: ${now.toLocaleTimeString()}`;
    }
    
    // Update app card status attribute for filtering
    card.dataset.status = data.docker_status || 'unknown';
  }
  
  /**
   * Get CSS class for Docker status
   * @param {string} status - Docker status
   * @returns {string} - CSS class
   */
  function getStatusClass(status) {
    if (!status) return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    
    switch (status.toLowerCase()) {
      case 'running':
        return 'px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded';
      case 'stopped':
      case 'exited':
        return 'px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded';
      case 'restarting':
        return 'px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded';
      default:
        return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    }
  }
  
  /**
   * Get CSS class for health status
   * @param {Object} data - Full status data
   * @param {string} status - Health status
   * @returns {string} - CSS class
   */
  function getHealthClass(data, status) {
    if (!status) return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    
    // If docker is not running, health is irrelevant
    if (data.docker_status && 
        ['stopped', 'exited'].includes(data.docker_status.toLowerCase())) {
      return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    }
    
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded';
      case 'unhealthy':
        return 'px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded';
      case 'starting':
        return 'px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded';
      default:
        return 'px-2 py-0.5 text-xs bg-gray-100 text-gray-800 rounded';
    }
  }
  
  /**
   * Show a toast notification (standalone function for batch operations)
   * @param {string} message - Message to display
   * @param {string} type - Notification type
   */
  function showToast(message, type = 'success') {
    if (!message) return;
    
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toastContainer';
      toastContainer.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
      document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `px-4 py-2 rounded-sm shadow-md text-sm ${
      type === 'success' ? 'bg-green-100 border border-green-300 text-green-800' :
      type === 'error' ? 'bg-red-100 border border-red-300 text-red-800' :
      'bg-blue-100 border border-blue-300 text-blue-800'
    }`;
    toast.innerText = message;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Remove after delay
    setTimeout(() => {
      toast.classList.add('opacity-0', 'transition-opacity', 'duration-500');
      setTimeout(() => {
        toast.remove();
        
        // Remove container if empty
        if (toastContainer.children.length === 0) {
          toastContainer.remove();
        }
      }, 500);
    }, 3000);
  }
  
  // Initialize batch operations
  document.addEventListener('DOMContentLoaded', () => {
    setupBatchOperations();
  });
  
  /**
   * Requirements Analyzer class
   * Handles the UI interactions for the requirements analysis tool
   */
  class RequirementsAnalyzer {
    constructor() {
      this.requirementsForm = document.getElementById('requirementsForm');
      this.toggleFormBtn = document.getElementById('toggleForm');
      this.searchInput = document.getElementById('searchIssues');
      this.severityFilter = document.getElementById('severityFilter');
      this.fileFilter = document.getElementById('fileFilter');
      this.progressBar = document.getElementById('progressBar');
      this.progressStatus = document.getElementById('progressStatus');
      this.progressInterval = null;
      
      this.initializeEventListeners();
      this.maybeShowForm();
      this.updateAnalysisDuration();
    }
    
    initializeEventListeners() {
      // Toggle requirements form
      if (this.toggleFormBtn) {
        this.toggleFormBtn.addEventListener('click', () => {
          if (!this.requirementsForm) return;
          
          this.requirementsForm.classList.toggle('hidden');
          this.toggleFormBtn.textContent = this.requirementsForm.classList.contains('hidden') 
            ? 'Show Requirements Form' 
            : 'Hide Requirements';
        });
      }
      
      // Initialize filter listeners
      if (this.searchInput) {
        this.searchInput.addEventListener('input', () => this.applyFilters());
      }
      
      if (this.severityFilter) {
        this.severityFilter.addEventListener('change', () => this.applyFilters());
      }
      
      if (this.fileFilter) {
        this.fileFilter.addEventListener('change', () => this.applyFilters());
      }
      
      // Setup expand/collapse buttons for issues
      document.querySelectorAll('.toggle-issue-details').forEach(button => {
        button.addEventListener('click', (e) => this.toggleIssueDetails(e.currentTarget));
      });
      
      // Setup analysis form submission
      const analysisForm = document.getElementById('requirementsForm');
      if (analysisForm) {
        analysisForm.addEventListener('submit', () => {
          this.startProgressIndicator();
        });
      }
    }
    
    startProgressIndicator() {
      if (!this.progressBar || !this.progressStatus) return;
      
      let progress = 0;
      const statuses = [
        'Analyzing code structure...',
        'Identifying requirements...',
        'Checking for implementation...',
        'Validating code quality...',
        'Finding potential issues...',
        'Generating recommendations...'
      ];
      
      // Reset progress bar
      this.progressBar.value = 0;
      this.progressBar.classList.remove('hidden');
      this.progressStatus.textContent = statuses[0];
      this.progressStatus.classList.remove('hidden');
      
      // Update progress bar at intervals
      this.progressInterval = setInterval(() => {
        progress += Math.random() * 3;
        this.progressBar.value = Math.min(progress, 95);
        
        if (progress <= 95) {
          const statusIndex = Math.floor(progress / 15) % statuses.length;
          this.progressStatus.textContent = statuses[statusIndex];
        }
        
        // Stop at 95% (the page reload will complete it)
        if (progress >= 95) {
          clearInterval(this.progressInterval);
        }
      }, 300);
    }
    
    toggleIssueDetails(button) {
      if (!button) return;
      
      const container = button.closest('div').nextElementSibling;
      if (!container) return;
      
      const details = container.querySelector('.issue-details');
      if (!details) return;
      
      details.classList.toggle('hidden');
      button.textContent = details.classList.contains('hidden') ? 'Expand' : 'Collapse';
    }
    
    applyFilters() {
      if (!this.searchInput || !this.severityFilter || !this.fileFilter) return;
      
      const searchTerm = this.searchInput.value.toLowerCase();
      const selectedSeverity = this.severityFilter.value;
      const selectedFile = this.fileFilter.value;
      let visibleCount = 0;
      
      document.querySelectorAll('#issueList > div').forEach(issue => {
        const severityMatch = selectedSeverity === 'all' || issue.dataset.severity === selectedSeverity;
        const fileMatch = selectedFile === 'all' || issue.dataset.file === selectedFile;
        const searchMatch = !searchTerm || issue.dataset.searchable.toLowerCase().includes(searchTerm);
        const isVisible = severityMatch && fileMatch && searchMatch;
        
        issue.style.display = isVisible ? 'block' : 'none';
        if (isVisible) visibleCount++;
      });
      
      // Update filters status
      const filterStatus = document.getElementById('filterStatus');
      if (filterStatus) {
        if (searchTerm || selectedSeverity !== 'all' || selectedFile !== 'all') {
          filterStatus.textContent = `Showing ${visibleCount} filtered results`;
          filterStatus.classList.remove('hidden');
        } else {
          filterStatus.classList.add('hidden');
        }
      }
    }
    
    updateAnalysisDuration() {
      const durationElement = document.getElementById('analysisDuration');
      if (!durationElement || !window.summary) return;
      
      if (window.summary.start_time && window.summary.end_time) {
        const start = new Date(window.summary.start_time);
        const end = new Date(window.summary.end_time);
        const seconds = Math.round((end - start) / 1000);
        durationElement.textContent = seconds + 's';
      } else {
        durationElement.textContent = 'N/A';
      }
    }
    
    maybeShowForm() {
      // Show form if no issues and no requirements
      const hasIssues = document.querySelectorAll('#issueList > div').length > 0;
      const hasRequirements = window.summary && 
                             window.summary.requirements && 
                             window.summary.requirements.length > 0;
      
      if (!hasIssues && !hasRequirements && this.requirementsForm) {
        this.requirementsForm.classList.remove('hidden');
        
        if (this.toggleFormBtn) {
          this.toggleFormBtn.textContent = 'Hide Requirements';
        }
      }
    }
  }
  