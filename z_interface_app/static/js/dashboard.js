/**
 * AI Model Management Dashboard
 * Object-Oriented JavaScript implementation using ES6 classes
 */

// Main Application Class
class Dashboard {
  /**
   * Initialize the dashboard application
   */
  constructor() {
    // Create configuration manager
    this.config = new ConfigurationManager();
    
    // Create services
    this.stateManager = new StateManager();
    this.apiService = new ApiService(this.config);
    this.utilityService = new UtilityService();
    
    // Create controllers that depend on services
    this.coreController = new CoreController(this);
    this.uiController = new UIController(this);
    
    // Create feature managers
    this.featureManager = new FeatureManager(this);
  }

  /**
   * Initialize the application and all components
   */
  init() {
    console.log('Initializing AI Model Management Dashboard');
    
    // Initialize components
    this.coreController.init();
    this.uiController.init();
    
    // Set up global event listeners
    this.setupGlobalListeners();
    
    // Initialize features if they exist on the current page
    this.featureManager.initFeatures();
  }

  /**
   * Set up global event handlers
   */
  setupGlobalListeners() {
    // Handle visibility change to manage auto-refresh
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.coreController.autoRefreshService.pause();
      } else {
        this.coreController.autoRefreshService.resume();
      }
    });
    
    // Set up global error handling
    window.addEventListener('error', this.utilityService.handleGlobalError.bind(this.utilityService));
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
      retryDelay: 1000
    };
    
    this.ui = {
      toastDuration: 3000
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
        this.autoRefresh.enabled = settings.autoRefresh?.enabled ?? false;
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
          enabled: this.autoRefresh.enabled
        }
      };
      localStorage.setItem('dashboardSettings', JSON.stringify(settings));
    } catch (e) {
      console.warn('Failed to save settings:', e);
    }
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
    this.activeFilters = {};
    this.autoRefreshPaused = false;
    this.currentAnalysis = null;
  }
}

/**
 * Core Controller Class
 * Manages core application functionality
 */
class CoreController {
  /**
   * @param {Dashboard} dashboard - Main dashboard instance
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
    this.dashboard.config.loadStoredSettings();
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
      console.error('Error refreshing statuses:', error);
      this.dashboard.utilityService.logError({
        message: 'Failed to refresh all statuses',
        error
      });
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
    if (!model || !appNum) return Promise.reject(new Error('Invalid parameters'));
    
    return $.ajax({
      url: `/status/${model}/${appNum}`,
      method: 'GET',
      dataType: 'json',
      cache: false,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .done(data => {
      this.dashboard.uiController.updateStatusDisplay(model, appNum, data);
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      console.error(`Error updating status for ${model} app ${appNum}:`, errorThrown);
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
    
    // Show special handling for rebuild which may take longer
    if (action === 'rebuild') {
      this.dashboard.uiController.showToast(`Rebuilding ${model} App ${appNum}. This may take several minutes...`, 'info');
    }
    
    return $.ajax({
      url: `/${action}/${model}/${appNum}`,
      method: 'GET',
      dataType: 'json',
      cache: false,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .done(result => {
      if (result && result.message) {
        console.log(`${action} result:`, result.message);
      }
      return true;
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      console.error(`Action '${action}' failed:`, errorThrown);
      throw new Error(`Failed to ${action}: ${errorThrown}`);
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
    
    // Initialize counters
    let success = 0;
    let failed = 0;
    let processed = 0;
    
    // Process apps in batches
    const batchSize = 3;
    const deferred = $.Deferred();
    const batchPromises = [];
    
    // Process each batch
    for (let i = 0; i < appNumbers.length; i += batchSize) {
      const batch = appNumbers.slice(i, i + batchSize);
      
      // Create promises for this batch
      const processBatch = () => {
        const promises = batch.map(appNum => {
          return this.processBatchOperation(action, model, appNum)
            .then(result => {
              processed++;
              if (result) success++;
              else failed++;
              
              // Update UI with progress
              this.dashboard.uiController.updateBatchProgress(model, action, processed, appNumbers.length);
              
              return result;
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
      this.dashboard.uiController.updateBatchResult(model, action, success, failed, appNumbers.length);
      
      // Refresh statuses
      setTimeout(() => {
        this.refreshAllStatuses();
      }, 1000);
      
      deferred.resolve({ success, failed, total: appNumbers.length });
    }).fail(error => {
      console.error('Batch operation failed:', error);
      deferred.reject(error);
    });
    
    return deferred.promise();
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
      return $.ajax({
        url: `/api/health/${model}/${appNum}`,
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(() => true)
      .fail(() => false);
    }
    
    // Handle standard actions with retry logic
    return this.dashboard.apiService.fetchWithRetry(`/${action}/${model}/${appNum}`)
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
   * @param {Dashboard} dashboard - Main dashboard instance
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
    if (this.dashboard.stateManager.autoRefreshPaused && this.dashboard.config.autoRefresh.enabled) {
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
   * @param {Dashboard} dashboard - Main dashboard instance
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
    $.ajax({
      url: '/api/system-info',
      method: 'GET',
      dataType: 'json',
      cache: false,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .done(data => {
      this.dashboard.uiController.updateSystemInfoDisplay(data);
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      console.error('Failed to load system info:', errorThrown);
    });
  }
}

/**
 * UI Controller Class
 * Manages UI interactions and updates
 */
class UIController {
  /**
   * @param {Dashboard} dashboard - Main dashboard instance
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
  }

  /**
   * Set up UI event listeners
   */
  setupEventListeners() {
    // Action buttons
    $(this.selectors.actionButtons).each((i, button) => {
      if (!$(button).data('action')) return;
      
      $(button).on('click', e => {
        this.handleActionButton(e);
      });
    });
    
    // Refresh all button
    $(this.selectors.refreshAllBtn).on('click', () => {
      this.dashboard.coreController.refreshAllStatuses();
    });
    
    // Toggle auto-refresh button
    $(this.selectors.toggleAutorefreshBtn).on('click', () => {
      this.dashboard.coreController.autoRefreshService.toggle();
    });
    
    // Batch menu buttons
    $(this.selectors.batchMenu).on('click', e => {
      e.stopPropagation();
      const $dropdown = $(e.currentTarget).next(this.selectors.batchMenuItems);
      
      $dropdown.toggleClass('hidden');
      
      // Close other open dropdowns
      $(this.selectors.batchMenuItems).not($dropdown).addClass('hidden');
    });
    
    // Close dropdowns when clicking elsewhere
    $(document).on('click', () => {
      $(this.selectors.batchMenuItems).addClass('hidden');
    });
    
    // Batch action buttons
    $(this.selectors.batchAction).on('click', e => {
      this.handleBatchAction(e);
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
    if (this.dashboard.stateManager.pendingActions.has(actionKey)) {
      console.log(`Action ${actionKey} already in progress, skipping`);
      return;
    }
    
    // Add to pending actions
    const originalText = button.textContent;
    this.dashboard.stateManager.pendingActions.set(actionKey, true);
    
    // Update button state
    button.disabled = true;
    button.innerHTML = this.getLoadingIndicator(action);
    
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
        this.dashboard.utilityService.logError({
          message: `Action '${action}' failed`,
          context: { action, model, appNum },
          error
        });
      })
      .always(() => {
        // Restore button state
        button.disabled = false;
        button.textContent = originalText;
        
        // Remove from pending actions
        this.dashboard.stateManager.pendingActions.delete(actionKey);
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
        
        this.dashboard.utilityService.logError({
          message: `Batch operation '${action}' failed`,
          context: { action, model },
          error
        });
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
      // Update status badges
      const $backendStatusEl = $appCard.find('[data-status="backend"]');
      const $frontendStatusEl = $appCard.find('[data-status="frontend"]');
      const $statusBadgeEl = $appCard.find('.status-badge');
      
      // Backend status
      if ($backendStatusEl.length) {
        $backendStatusEl.text(data.backend_status?.running ? 'Running' : 'Stopped');
        $backendStatusEl.attr('class', data.backend_status?.running ? 'font-medium text-green-700' : 'font-medium text-red-700');
      }
      
      // Frontend status
      if ($frontendStatusEl.length) {
        $frontendStatusEl.text(data.frontend_status?.running ? 'Running' : 'Stopped');
        $frontendStatusEl.attr('class', data.frontend_status?.running ? 'font-medium text-green-700' : 'font-medium text-red-700');
      }
      
      // Overall status badge
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
      
      // Update last updated time
      const $lastUpdateEl = $appCard.find('[data-last-update]');
      if ($lastUpdateEl.length) {
        const now = new Date();
        $lastUpdateEl.text(`Last updated: ${now.toLocaleTimeString()}`);
        $lastUpdateEl.data('timestamp', now.getTime());
      }
      
      // Update metrics if available
      if (data.metrics) {
        this.updateMetricsDisplay($appCard, data.metrics);
      }
    } catch (error) {
      console.error('Error updating status display:', error);
    }
  }

  /**
   * Update metrics display for an app
   * @param {HTMLElement} card - App card element
   * @param {Object} metrics - Metrics data
   */
  updateMetricsDisplay(card, metrics) {
    if (!card || !metrics) return;
    
    // CPU usage
    const $cpuEl = $(card).find('.metric-cpu');
    if ($cpuEl.length && metrics.cpu_percent !== undefined) {
      $cpuEl.text(`${metrics.cpu_percent.toFixed(1)}%`);
    }
    
    // Memory usage
    const $memEl = $(card).find('.metric-memory');
    if ($memEl.length && metrics.memory_usage !== undefined) {
      $memEl.text(this.dashboard.utilityService.formatBytes(metrics.memory_usage));
    }
    
    // Request count
    const $requestsEl = $(card).find('.metric-requests');
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
    
    // CPU usage
    const $cpuEl = $('#systemCpuUsage');
    if ($cpuEl.length && data.cpu_percent !== undefined) {
      $cpuEl.text(`${data.cpu_percent.toFixed(1)}%`);
      
      $cpuEl.attr('class', data.cpu_percent > 80 
        ? 'text-red-600 font-medium' 
        : data.cpu_percent > 50 
          ? 'text-yellow-600 font-medium' 
          : 'text-green-600 font-medium');
    }
    
    // Memory usage
    const $memEl = $('#systemMemoryUsage');
    if ($memEl.length && data.memory_percent !== undefined) {
      $memEl.text(`${data.memory_percent.toFixed(1)}%`);
      
      $memEl.attr('class', data.memory_percent > 85 
        ? 'text-red-600 font-medium' 
        : data.memory_percent > 70 
          ? 'text-yellow-600 font-medium' 
          : 'text-green-600 font-medium');
    }
    
    // Disk usage
    const $diskEl = $('#systemDiskUsage');
    if ($diskEl.length && data.disk_percent !== undefined) {
      $diskEl.text(`${data.disk_percent.toFixed(1)}%`);
      
      $diskEl.attr('class', data.disk_percent > 90 
        ? 'text-red-600 font-medium' 
        : data.disk_percent > 75 
          ? 'text-yellow-600 font-medium' 
          : 'text-green-600 font-medium');
    }
    
    // System uptime
    const $uptimeEl = $('#systemUptime');
    if ($uptimeEl.length && data.uptime_seconds !== undefined) {
      $uptimeEl.text(this.dashboard.utilityService.formatUptime(data.uptime_seconds));
    }
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
   * Get loading indicator HTML
   * @param {string} action - Action being performed
   * @returns {string} - HTML for the loading indicator
   */
  getLoadingIndicator(action) {
    return `<svg class="inline-block w-4 h-4 mr-1 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>${this.dashboard.utilityService.capitalizeFirst(action)}ing...`;
  }

  /**
   * Show a toast notification
   * @param {string} message - Message to display
   * @param {string} type - Notification type (success, error, info)
   * @returns {HTMLElement} - Toast element
   */
  showToast(message, type = 'success') {
    if (!message) return;
    
    // Create toast container if it doesn't exist
    let $toastContainer = $('#toastContainer');
    if ($toastContainer.length === 0) {
      $toastContainer = $('<div>', {
        id: 'toastContainer',
        class: 'fixed bottom-4 right-4 z-50 flex flex-col gap-2'
      }).appendTo('body');
    }
    
    // Create toast element
    const $toast = $('<div>', {
      class: `px-4 py-2 rounded-sm shadow-md text-sm transition-opacity duration-300 ${
        type === 'success' ? 'bg-green-100 border border-green-300 text-green-800' :
        type === 'error' ? 'bg-red-100 border border-red-300 text-red-800' :
        'bg-blue-100 border border-blue-300 text-blue-800'
      }`,
      text: message
    });
    
    // Add to container
    $toastContainer.append($toast);
    
    // Remove after delay
    setTimeout(() => {
      $toast.css('opacity', 0);
      setTimeout(() => {
        $toast.remove();
      }, 300);
    }, this.dashboard.config.ui.toastDuration);
    
    return $toast;
  }
}

/**
 * API Service Class
 * Handles network requests and data handling
 */
class ApiService {
  /**
   * @param {ConfigurationManager} config - Configuration instance
   */
  constructor(config) {
    this.config = config;
  }

  /**
   * Fetch with retry logic
   * @param {string} url - URL to fetch
   * @param {Object} options - Fetch options
   * @param {number} retries - Number of retries
   * @returns {Promise} - Promise for the request
   */
  fetchWithRetry(url, options = {}, retries = null) {
    if (retries === null) {
      retries = this.config.api.retryAttempts;
    }
    
    // Default headers
    const headers = {
      'X-Requested-With': 'XMLHttpRequest',
      'Cache-Control': 'no-cache'
    };
    
    // Default request options
    const ajaxOptions = Object.assign({
      url: url,
      headers: headers,
      method: options.method || 'GET',
      dataType: options.dataType || 'json'
    }, options);
    
    // Remove invalid options
    delete ajaxOptions.retries;
    
    // Ensure URL is valid
    if (url.includes('/undefined')) {
      return $.Deferred().reject(new Error(`Invalid URL: ${url}`));
    }
    
    // Function to attempt the request
    const attemptRequest = remainingRetries => {
      return $.ajax(ajaxOptions)
        .fail((jqXHR, textStatus, errorThrown) => {
          if (remainingRetries <= 0) {
            return $.Deferred().reject(errorThrown || textStatus);
          }
          
          console.warn(`API request attempt failed (${retries - remainingRetries + 1}/${retries}):`, textStatus);
          
          // Wait before retry using exponential backoff
          const delay = this.config.api.retryDelay * Math.pow(2, retries - remainingRetries);
          
          return new Promise(resolve => setTimeout(resolve, delay))
            .then(() => {
              return attemptRequest(remainingRetries - 1);
            });
        });
    };
    
    return attemptRequest(retries);
  }
}

/**
 * Utility Service Class
 * Provides helper functions
 */
class UtilityService {
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
   * Handle global errors
   * @param {Event} event - Error event
   * @returns {boolean} - Whether to prevent default handling
   */
  handleGlobalError(event) {
    const errorDetails = {
      message: event.originalEvent?.message || 'Unknown error',
      filename: event.originalEvent?.filename,
      lineno: event.originalEvent?.lineno,
      colno: event.originalEvent?.colno,
      stack: event.originalEvent?.error ? event.originalEvent.error.stack : 'No stack trace',
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };
    
    console.error('CLIENT ERROR:', errorDetails);
    
    // Send error to server for logging
    $.ajax({
      url: '/api/log-client-error',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(errorDetails)
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      console.error('Failed to send error to server:', errorThrown);
    });
    
    return true; // Prevent default error handling
  }

  /**
   * Log error to server
   * @param {Object} errorData - Error data to log
   */
  logError(errorData) {
    if (!errorData) return;
    
    const enhancedErrorData = {
      ...errorData,
      error: errorData.error ? errorData.error.toString() : 'Unknown error',
      stack: errorData.error?.stack || 'No stack trace',
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };
    
    console.error('CLIENT ERROR:', enhancedErrorData);
    
    // Send to server
    $.ajax({
      url: '/api/log-client-error',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(enhancedErrorData)
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      console.error('Failed to send error to server:', errorThrown);
    });
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
    this.securityAnalysis = new SecurityAnalysis(dashboard);
    this.performanceTest = new PerformanceTest(dashboard);
    this.requirementsAnalysis = new RequirementsAnalysis(dashboard);
    this.securityAnalysisPage = new SecurityAnalysisPage(dashboard);
    this.zapScan = new ZapScan(dashboard);
  }

  /**
   * Initialize features based on page elements
   */
  initFeatures() {
    // Security Analysis
    if (document.querySelector('.security-scan-btn')) {
      this.securityAnalysis.init();
    }
    
    // Performance Test
    if (document.getElementById('runTest')) {
      this.performanceTest.init();
    }
    
    // Requirements Analysis
    if (document.querySelector('form') && document.getElementById('submitBtn')) {
      this.requirementsAnalysis.init();
    }
    
    // Security Analysis Page
    if (document.getElementById('searchIssues') && document.getElementById('riskFilter')) {
      this.securityAnalysisPage.init();
    }
    
    // ZAP Scan
    if (document.getElementById('startScan')) {
      this.zapScan.init();
    }
  }
}

/**
 * Security Analysis Feature Class
 * Handles security analysis functionality
 */
class SecurityAnalysis {
  /**
   * @param {Dashboard} dashboard - Main dashboard instance
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
    document.querySelectorAll('.security-scan-btn').forEach(button => {
      button.addEventListener('click', this.handleScanClick.bind(this));
    });
    
    // Setup modal close buttons
    document.querySelectorAll('.modal-close').forEach(button => {
      button.addEventListener('click', () => {
        document.getElementById('securityModal').classList.add('hidden');
      });
    });
    
    // Setup start analysis button
    const startAnalysisBtn = document.getElementById('startAnalysis');
    if (startAnalysisBtn) {
      startAnalysisBtn.addEventListener('click', this.startAnalysis.bind(this));
    }
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
    
    // Run analysis
    $.ajax({
      url: '/api/security/analyze-file',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        model: model,
        app_num: appNum,
        analysis_type: analysisType,
        ai_model: aiModel
      })
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
    .fail((jqXHR, textStatus, errorThrown) => {
      this.dashboard.uiController.showToast(`Analysis failed: ${errorThrown}`, 'error');
      document.getElementById('scanLoading').classList.add('hidden');
      
      this.dashboard.utilityService.logError({
        message: 'Security analysis failed',
        context: { model, appNum, analysisType, aiModel },
        error: errorThrown
      });
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
    $.ajax({
      url: '/api/security/global-summary',
      method: 'GET',
      dataType: 'json'
    })
    .done(data => {
      // Update global counters
      const highIssuesEl = document.getElementById('totalHighIssues');
      const mediumIssuesEl = document.getElementById('totalMediumIssues');
      const lowIssuesEl = document.getElementById('totalLowIssues');
      const lastGlobalScanEl = document.getElementById('lastGlobalScan');
      
      if (highIssuesEl) highIssuesEl.textContent = data.totals?.high || 0;
      if (mediumIssuesEl) mediumIssuesEl.textContent = data.totals?.medium || 0;
      if (lowIssuesEl) lowIssuesEl.textContent = data.totals?.low || 0;
      if (lastGlobalScanEl) {
        lastGlobalScanEl.textContent = data.last_scan 
          ? new Date(data.last_scan).toLocaleString() 
          : 'Never';
      }
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      console.error('Failed to load security summary:', errorThrown);
    });
  }
}

/**
 * Performance Test Feature Class
 * Handles performance testing functionality
 */
class PerformanceTest {
  /**
   * @param {Dashboard} dashboard - Main dashboard instance
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
    const runTestBtn = document.getElementById('runTest');
    const stopTestBtn = document.getElementById('stopTest');
    const clearLogBtn = document.getElementById('clearLog');
    
    if (runTestBtn) {
      runTestBtn.addEventListener('click', this.runTest.bind(this));
    }
    
    if (stopTestBtn) {
      stopTestBtn.addEventListener('click', this.stopTest.bind(this));
    }
    
    if (clearLogBtn) {
      clearLogBtn.addEventListener('click', () => {
        document.getElementById('outputLog').textContent = '';
      });
    }
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
    $.ajax({
      url: window.location.href,
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        num_users: numUsers,
        duration: duration,
        spawn_rate: spawnRate,
        endpoints: ["/", "/api/status"]
      })
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
    .fail((jqXHR, textStatus, errorThrown) => {
      document.getElementById('progressBar').style.width = '0%';
      document.getElementById('testStatus').textContent = 'Failed';
      this.appendToLog(`Error: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
      this.dashboard.uiController.showToast(`Test failed: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`, 'error');
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
    
    $.ajax({
      url: `${window.location.href}/stop`,
      method: 'POST'
    })
    .done(() => {
      this.appendToLog('Test stopped successfully');
      document.getElementById('testStatus').textContent = 'Stopped';
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      this.appendToLog(`Failed to stop test: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
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
    document.getElementById('progressBar').style.width = '0%';
    
    const timer = setInterval(() => {
      elapsed += interval;
      const percentage = Math.min(Math.floor((elapsed / (duration * 1000)) * 100), 95);
      document.getElementById('progressBar').style.width = `${percentage}%`;
      
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
      const element = document.getElementById(id);
      if (element) {
        element.textContent = value;
      }
    });
    
    // Update endpoint table
    this.updateEndpointTable(data.endpoints || []);
    
    // Update error table
    this.updateErrorTable(data.errors || []);
    
    // Show/hide visualization
    const visualizationSection = document.getElementById('visualizationSection');
    if (visualizationSection) {
      visualizationSection.classList.toggle('hidden', !(data.endpoints && data.endpoints.length > 0));
    }
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
   * @param {Dashboard} dashboard - Main dashboard instance
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
    $('.hover\\:bg-gray-50').on('click', function() {
      const detailId = $(this).attr('onclick')?.match(/toggleDetails\('([^']+)'\)/)?.[1];
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
      $form.on('submit', function() {
        $submitBtn.html(`
          <svg class="animate-spin w-3 h-3 inline mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>Checking...`);
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
   * @param {Dashboard} dashboard - Main dashboard instance
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
    $('.expand-btn').on('click', function() {
      const $details = $(this).closest('div').next().find('.alert-details');
      $details.toggleClass('hidden');
      $(this).text($details.hasClass('hidden') ? 'Expand' : 'Collapse');
    });
  }
}

/**
 * ZAP Scan Feature Class
 * Handles ZAP scanning functionality
 */
class ZapScan {
  /**
   * @param {Dashboard} dashboard - Main dashboard instance
   */
  constructor(dashboard) {
    this.dashboard = dashboard;
    this.pollingActive = false;
    this.pollingErrorCount = 0;
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
    const startScanBtn = document.getElementById('startScan');
    const stopScanBtn = document.getElementById('stopScan');
    const clearLogBtn = document.getElementById('clearLog');
    
    if (startScanBtn) {
      startScanBtn.addEventListener('click', this.startScan.bind(this));
    }
    
    if (stopScanBtn) {
      stopScanBtn.addEventListener('click', this.stopScan.bind(this));
    }
    
    if (clearLogBtn) {
      clearLogBtn.addEventListener('click', () => {
        document.getElementById('progressLog').textContent = '';
      });
    }
    
    // Add this new code for expand buttons
    document.addEventListener('click', (event) => {
      // Check if the clicked element is an expand button
      if (event.target.classList.contains('expand-btn')) {
        // Find the details container within the alert item
        const alertItem = event.target.closest('.alert-item');
        if (!alertItem) return;
        
        const details = alertItem.querySelector('.alert-details');
        if (!details) return;
        
        // Toggle visibility
        if (details.classList.contains('hidden')) {
          details.classList.remove('hidden');
          event.target.textContent = 'Collapse';
        } else {
          details.classList.add('hidden');
          event.target.textContent = 'Expand';
        }
      }
    });
  }

  /**
   * Update target URL display
   */
  updateTargetUrl() {
    // Extract model and app from URL
    const urlParts = window.location.pathname.split('/');
    const model = urlParts[urlParts.length - 2] || '';
    const appNum = urlParts[urlParts.length - 1] || '';
    
    // Calculate port using the logic from the original code
    const port = this.calculatePort(model, parseInt(appNum));
    
    const targetUrlElement = document.getElementById('targetUrl');
    if (targetUrlElement) {
      targetUrlElement.textContent = `http://localhost:${port}`;
    }
  }

  /**
   * Calculate port based on model and app number
   * @param {string} model - Model name
   * @param {number} appNum - App number
   * @returns {number} - Calculated port
   */
  calculatePort(model, appNum) {
    // Constants matching those in app.py PortManager
    const BASE_FRONTEND_PORT = 5501;
    const PORTS_PER_APP = 2;
    const BUFFER_PORTS = 20;
    const APPS_PER_MODEL = 30;
    const TOTAL_PORTS_PER_MODEL = APPS_PER_MODEL * PORTS_PER_APP + BUFFER_PORTS;
    
    // AI_MODELS array from app.py for model indexing
    const AI_MODELS = [
      "Llama", "Mistral", "DeepSeek", "GPT4o", "Claude", 
      "Gemini", "Grok", "R1", "O3"
    ];
    
    // Get model index (0-based)
    let modelIdx = AI_MODELS.indexOf(model);
    if (modelIdx === -1) {
      console.warn(`Model "${model}" not found in AI_MODELS list. Using default index 0.`);
      modelIdx = 0;
    }
    
    // Calculate frontend port using the same logic as PortManager.get_app_ports
    const frontendPortRangeStart = BASE_FRONTEND_PORT + (modelIdx * TOTAL_PORTS_PER_MODEL);
    const port = frontendPortRangeStart + ((appNum - 1) * PORTS_PER_APP);
    
    return port;
  }

  /**
   * Start ZAP scan
   */
  startScan() {
    // Get model and app from URL
    const urlParts = window.location.pathname.split('/');
    const model = urlParts[urlParts.length - 2] || '';
    const appNum = urlParts[urlParts.length - 1] || '';
    
    // Get scan options
    const scanOptions = {
      spiderDepth: parseInt(document.getElementById('spiderDepth')?.value) || 5,
      threadCount: parseInt(document.getElementById('threadCount')?.value) || 2,
      useAjaxSpider: document.getElementById('ajaxSpider')?.checked || false,
      usePassiveScan: document.getElementById('passiveScan')?.checked || true,
      useActiveScan: document.getElementById('activeScan')?.checked || true,
      scanPolicy: document.getElementById('scanPolicy')?.value || 'Default Policy'
    };
    
    // Update UI for scan start
    document.getElementById('startScan').disabled = true;
    document.getElementById('stopScan').classList.remove('hidden');
    document.getElementById('scanStatus').textContent = 'Starting...';
    document.getElementById('scanProgress').classList.remove('hidden');
    
    this.appendToLog(`Starting scan with options: Spider Depth=${scanOptions.spiderDepth}, Threads=${scanOptions.threadCount}, AJAX=${scanOptions.useAjaxSpider}`);
    
    // Start the scan
    $.ajax({
      url: `/zap/scan/${model}/${appNum}`,
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(scanOptions)
    })
    .done(() => {
      this.appendToLog('Scan started successfully');
      this.pollProgress(model, appNum);
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      this.appendToLog(`Error: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
      document.getElementById('scanStatus').textContent = 'Error';
      document.getElementById('startScan').disabled = false;
      document.getElementById('stopScan').classList.add('hidden');
      this.dashboard.uiController.showToast(`Failed to start scan: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`, 'error');
    });
  }

  /**
   * Stop ZAP scan
   */
  stopScan() {
    // Get model and app from URL
    const urlParts = window.location.pathname.split('/');
    const model = urlParts[urlParts.length - 2] || '';
    const appNum = urlParts[urlParts.length - 1] || '';
    
    this.appendToLog('Stopping scan...');
    
    $.ajax({
      url: `/zap/scan/${model}/${appNum}/stop`,
      method: 'POST'
    })
    .done(() => {
      this.appendToLog('Scan stopped successfully');
      document.getElementById('scanStatus').textContent = 'Stopped';
      document.getElementById('startScan').disabled = false;
      document.getElementById('stopScan').classList.add('hidden');
    })
    .fail((jqXHR, textStatus, errorThrown) => {
      this.appendToLog(`Error stopping scan: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
      this.dashboard.uiController.showToast(`Failed to stop scan: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`, 'error');
    });
  }

  /**
   * Poll scan progress
   * @param {string} model - Model name
   * @param {string|number} appNum - App number
   */
  pollProgress(model, appNum) {
    this.pollingActive = true;
    this.pollingErrorCount = 0;
    
    const updateUI = () => {
      $.ajax({
        url: `/zap/scan/${model}/${appNum}/status`,
        method: 'GET',
        dataType: 'json'
      })
      .done(data => {
        // Update progress bar
        document.getElementById('progressBar').style.width = `${Math.min(Math.max(data.progress, 0), 100)}%`;
        
        // Update status text
        document.getElementById('scanStatus').textContent = data.status || 'Unknown';
        
        // Update count elements
        document.getElementById('highCount').textContent = data.high_count || 0;
        document.getElementById('mediumCount').textContent = data.medium_count || 0;
        document.getElementById('lowCount').textContent = data.low_count || 0;
        document.getElementById('infoCount').textContent = data.info_count || 0;
        
        // Log important state changes
        if (data.status !== 'Running' && data.status !== 'Starting') {
          this.appendToLog(`Status changed to: ${data.status}`);
        }
        
        // Check if scan is complete
        if (data.status === 'Complete') {
          this.pollingActive = false;
          
          document.getElementById('stopScan').classList.add('hidden');
          document.getElementById('startScan').disabled = false;
          
          const lastScanTimeEl = document.getElementById('lastScanTime');
          if (lastScanTimeEl) {
            lastScanTimeEl.textContent = new Date().toLocaleString();
          }
          
          this.appendToLog('Scan completed. Reloading page to show results...');
          setTimeout(() => {
            window.location.reload();
          }, 1000);
          return;
        }
        
        // Continue polling if still active
        if (this.pollingActive) {
          setTimeout(updateUI, 2000);
        }
      })
      .fail((jqXHR, textStatus, errorThrown) => {
        console.error('Polling error:', errorThrown);
        this.appendToLog(`Error updating status: ${errorThrown || textStatus}`);
        
        // Increment error count
        this.pollingErrorCount++;
        
        // Stop polling after too many errors
        if (this.pollingErrorCount >= 3) {
          this.pollingActive = false;
          this.appendToLog('Stopped polling due to repeated errors');
          return;
        }
        
        // Retry with longer delay on error
        if (this.pollingActive) {
          setTimeout(updateUI, 5000);
        }
      });
    };
    
    // Start the polling loop
    updateUI();
  }

  /**
   * Append message to log
   * @param {string} message - Message to append
   */
  appendToLog(message) {
    const progressLog = document.getElementById('progressLog');
    if (!progressLog) return;
    
    const timestamp = new Date().toLocaleTimeString();
    progressLog.textContent += `[${timestamp}] ${message}\n`;
    progressLog.scrollTop = progressLog.scrollHeight;
  }
}

// Initialize the application when the DOM is ready
$(document).ready(function() {
  // Create dashboard instance
  window.dashboardApp = new Dashboard();
  
  // Initialize the dashboard
  window.dashboardApp.init();
});