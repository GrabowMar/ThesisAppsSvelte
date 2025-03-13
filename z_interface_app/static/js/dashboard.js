/**
 * AI Model Management Dashboard
 * Main controller for dashboard functionality
 */
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = new DashboardController();
  dashboard.init();
});

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
    const refreshBtn = document.getElementById('refreshAll');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', this.refreshAllStatuses.bind(this));
    }

    // Auto-refresh toggle
    const autoRefreshBtn = document.getElementById('toggleAutorefresh');
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
   * Handle action button clicks (start, stop, reload, etc.)
   * @param {Event} event - Click event
   */
  async handleAction(event) {
    const button = event.currentTarget;
    const { action, model, appNum } = button.dataset;
    
    // Prevent duplicate actions
    const actionKey = `${action}-${model}-${appNum}`;
    if (this.state.pendingActions.has(actionKey)) return;
    
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
    } finally {
      button.disabled = false;
      button.textContent = originalText;
      this.state.pendingActions.delete(actionKey);
    }
  }

  /**
   * Perform an action via API
   * @param {string} action - The action to perform
   * @param {string} model - The model name
   * @param {string} appNum - The app number
   * @returns {Promise<boolean>} - Success status
   */
  async performAction(action, model, appNum) {
    const response = await fetch(`/${action}/${model}/${appNum}`, {
      headers: { 
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache'
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Action failed: ${response.statusText}`);
    }
    
    return true;
  }

  /**
   * Handle quick actions (system-wide operations)
   * @param {Event} event - Click event
   */
  async handleQuickAction(event) {
    const button = event.currentTarget;
    const action = button.dataset.quickAction;
    const originalText = button.textContent;
    
    try {
      button.disabled = true;
      button.innerHTML = this.getLoadingSpinner();
      
      const response = await fetch(`/api/quick-action/${action}`, {
        method: 'POST',
        headers: { 
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json' 
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Action failed');
      }
      
      await this.refreshAllStatuses();
      this.showToast(`${this.capitalizeFirst(action)} completed`);
    } catch (error) {
      console.error(`Quick action '${action}' failed:`, error);
      this.showToast(error.message || `Failed to ${action}`, 'error');
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  }

  /**
   * Update the status of a specific app
   * @param {string} model - The model name
   * @param {string} appNum - The app number
   */
  async updateAppStatus(model, appNum) {
    try {
      const response = await fetch(`/api/container/${model}/${appNum}/status`);
      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.statusText}`);
      }

      const data = await response.json();
      const appCard = document.querySelector(`[data-app-id="${appNum}"][data-model="${model}"]`);
      if (appCard) this.updateStatusUI(appCard, data);
      
      return true;
    } catch (error) {
      console.error(`Status update failed for ${model}/${appNum}:`, error);
      return false;
    }
  }

  /**
   * Update the UI of an app card with status information
   * @param {HTMLElement} appCard - The app card element
   * @param {Object} status - Status information
   */
  updateStatusUI(appCard, status) {
    // Backend status
    const backendStatus = appCard.querySelector('[data-status="backend"]');
    if (backendStatus) {
      backendStatus.textContent = status.backend.running ? 'Running' : 'Stopped';
      backendStatus.className = `font-medium ${status.backend.running ? 'text-green-700' : 'text-red-700'}`;
    }

    // Frontend status
    const frontendStatus = appCard.querySelector('[data-status="frontend"]');
    if (frontendStatus) {
      frontendStatus.textContent = status.frontend.running ? 'Running' : 'Stopped';
      frontendStatus.className = `font-medium ${status.frontend.running ? 'text-green-700' : 'text-red-700'}`;
    }

    // Overall status badge
    const isRunning = status.backend.running && status.frontend.running;
    const isPartial = status.backend.running || status.frontend.running;
    const statusBadge = appCard.querySelector('.status-badge');
    
    if (statusBadge) {
      statusBadge.className = `status-badge text-xs px-2 py-0.5 border ${
        isRunning ? 'bg-green-100 text-green-800 border-green-700' :
        isPartial ? 'bg-yellow-100 text-yellow-800 border-yellow-700' :
        'bg-red-100 text-red-800 border-red-700'
      }`;
      statusBadge.textContent = isRunning ? 'Running' : isPartial ? 'Partial' : 'Stopped';
    }
  }

  /**
   * Refresh the status of all apps
   */
  async refreshAllStatuses() {
    // Prevent concurrent refreshes
    if (this.state.isRefreshing) return;
    
    const refreshBtn = document.getElementById('refreshAll');
    if (!refreshBtn) return;
    
    const originalText = refreshBtn.textContent;
    this.state.isRefreshing = true;

    try {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = this.getLoadingSpinner();

      const apps = document.querySelectorAll(this.selectors.appCards);
      const updatePromises = [...apps].map(app => 
        this.updateAppStatus(app.dataset.model, app.dataset.appId)
      );
      
      // Allow partial success - proceed even if some updates fail
      await Promise.allSettled(updatePromises);
      
      this.updateSystemInfo();
      this.state.lastRefreshTime = new Date();
      this.showToast('All statuses refreshed');
    } catch (error) {
      console.error('Failed to refresh statuses:', error);
      this.showToast('Failed to refresh some statuses', 'error');
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = originalText;
      this.state.isRefreshing = false;
    }
  }

  /**
   * Set up filtering functionality
   */
  setupFilters() {
    const searchInput = document.getElementById(this.selectors.searchApps.substring(1));
    const modelFilter = document.getElementById(this.selectors.filterModel.substring(1));
    const statusFilter = document.getElementById(this.selectors.filterStatus.substring(1));

    // Define filter function
    const applyFilters = this.debounce(() => {
      const searchTerm = searchInput?.value.toLowerCase() || '';
      const modelValue = modelFilter?.value || '';
      const statusValue = statusFilter?.value || '';

      // Count total apps and filtered apps for metrics
      let totalApps = 0;
      let filteredApps = 0;

      // Apply filters to each app card
      document.querySelectorAll(this.selectors.appCards).forEach(app => {
        totalApps++;
        const matchesSearch = searchTerm === '' || app.textContent.toLowerCase().includes(searchTerm);
        const matchesModel = modelValue === '' || app.dataset.model === modelValue;
        const matchesStatus = statusValue === '' || this.getAppStatus(app) === statusValue;
        
        const isVisible = matchesSearch && matchesModel && matchesStatus;
        app.style.display = isVisible ? '' : 'none';
        
        if (isVisible) filteredApps++;
      });

      this.updateModelSections();
      console.log(`Filtered apps: ${filteredApps}/${totalApps}`);
    }, 300);

    // Add event listeners
    [searchInput, modelFilter, statusFilter].forEach(filter => {
      if (filter) {
        filter.addEventListener('change', applyFilters);
      }
    });

    // Add input event for search field (real-time filtering)
    if (searchInput) {
      searchInput.addEventListener('input', applyFilters);
    }
  }

  /**
   * Update system info display
   */
  updateSystemInfo() {
    const healthStatus = document.querySelector(this.selectors.healthStatus);
    const dockerStatus = document.querySelector(this.selectors.dockerStatus); 
    const lastUpdate = document.querySelector(this.selectors.lastUpdate);

    if (healthStatus) healthStatus.textContent = 'Healthy';
    if (dockerStatus) dockerStatus.textContent = 'Connected';
    if (lastUpdate) lastUpdate.textContent = new Date().toLocaleString();
  }

  /**
   * Set up auto-refresh based on initial state
   */
  setupAutoRefresh() {
    const button = document.getElementById(this.selectors.toggleAutorefresh.substring(1));
    if (button && button.dataset.enabled === 'true') {
      this.startAutoRefresh();
    }
  }

  /**
   * Toggle auto-refresh on/off
   */
  toggleAutoRefresh() {
    const button = document.getElementById(this.selectors.toggleAutorefresh.substring(1));
    if (!button) return;
    
    const textSpan = button.querySelector(this.selectors.autorefreshText);
    const isEnabled = button.dataset.enabled === 'true';

    if (isEnabled) {
      this.stopAutoRefresh();
      button.dataset.enabled = 'false';
      if (textSpan) textSpan.textContent = 'Auto Refresh: Off';
    } else {
      this.startAutoRefresh();
      button.dataset.enabled = 'true';
      if (textSpan) textSpan.textContent = 'Auto Refresh: On';
    }
  }

  /**
   * Start auto-refresh interval
   */
  startAutoRefresh() {
    // Clear any existing interval first
    this.stopAutoRefresh();
    
    // Initial refresh
    this.refreshAllStatuses();
    
    // Set up interval
    this.config.autoRefreshInterval = setInterval(() => {
      if (!document.hidden) {
        this.refreshAllStatuses();
      }
    }, this.config.autoRefreshDuration);
  }

  /**
   * Stop auto-refresh interval
   */
  stopAutoRefresh() {
    if (this.config.autoRefreshInterval) {
      clearInterval(this.config.autoRefreshInterval);
      this.config.autoRefreshInterval = null;
    }
  }

  /**
   * Pause auto-refresh (without changing user preference)
   */
  pauseAutoRefresh() {
    if (this.config.autoRefreshInterval) {
      clearInterval(this.config.autoRefreshInterval);
      this.config.autoRefreshInterval = null;
    }
  }

  /**
   * Resume auto-refresh if it was previously enabled
   */
  resumeAutoRefresh() {
    const button = document.getElementById(this.selectors.toggleAutorefresh.substring(1));
    if (button && button.dataset.enabled === 'true' && !this.config.autoRefreshInterval) {
      this.startAutoRefresh();
    }
  }

  /**
   * Show a toast notification
   * @param {string} message - Message to display
   * @param {string} type - Notification type (success or error)
   */
  showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white
        ${type === 'error' ? 'bg-red-500' : 'bg-green-500'}`;
    toast.textContent = message;
    
    // Remove any existing toasts
    document.querySelectorAll('.fixed.bottom-4.right-4').forEach(el => el.remove());
    
    // Add and remove after timeout
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.5s';
      setTimeout(() => toast.remove(), 500);
    }, this.config.toastDuration);
  }

  /**
   * Get HTML for a loading spinner
   * @param {string} action - Optional action text
   * @returns {string} - HTML for spinner
   */
  getLoadingSpinner(action = 'Working') {
    return `<svg class="w-3 h-3 animate-spin mr-1 inline" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
    </svg>${action}...`;
  }

  /**
   * Get the status of an app card
   * @param {HTMLElement} app - App card element
   * @returns {string} - Status text
   */
  getAppStatus(app) {
    const status = app.querySelector('.status-badge')?.textContent.toLowerCase();
    return status || '';
  }

  /**
   * Update visibility of model sections based on filtered apps
   */
  updateModelSections() {
    // Hide model sections with no visible apps
    document.querySelectorAll(this.selectors.modelSections).forEach(section => {
      const hasVisibleApps = [...section.querySelectorAll(this.selectors.appCards)]
        .some(app => app.style.display !== 'none');
      section.style.display = hasVisibleApps ? '' : 'none';
    });

    // Toggle "no results" message
    const noResults = document.getElementById(this.selectors.noResultsMessage.substring(1));
    if (noResults) {
      const hasAnyVisible = document.querySelector(`${this.selectors.appCards}:not([style*="display: none"])`);
      noResults.classList.toggle('hidden', !!hasAnyVisible);
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
   * Log initialization information
   */
  logInitialization() {
    console.log('AI Model Management Dashboard initialized');
    console.log('Auto-refresh interval:', this.config.autoRefreshDuration / 1000, 'seconds');
  }
}


/**
 * GPT4All Requirements Analysis UI
 * 
 * This script handles the UI interactions for the requirements analysis tool,
 * including form toggling, filtering, progress tracking, and dynamic updates.
 */

class RequirementsAnalyzer {
  constructor() {
    // UI Elements
    this.form = document.querySelector('form');
    this.requirementsForm = document.getElementById('requirementsForm');
    this.toggleFormBtn = document.getElementById('toggleForm');
    this.cancelBtn = document.getElementById('cancelBtn');
    this.submitBtn = document.getElementById('submitBtn');
    this.btnText = document.getElementById('btnText');
    this.btnLoading = document.getElementById('btnLoading');
    this.progressBar = document.getElementById('progressBar');
    this.progressStatus = document.getElementById('progressStatus');
    this.analysisProgress = document.getElementById('analysisProgress');
    
    // Filters
    this.searchInput = document.getElementById('searchIssues');
    this.severityFilter = document.getElementById('severityFilter');
    this.fileFilter = document.getElementById('fileFilter');
    
    // Initialize event listeners
    this.initEventListeners();
    
    // Auto-show form if needed
    this.maybeShowForm();
    
    // Calculate and display analysis duration
    this.updateAnalysisDuration();
  }

  initEventListeners() {
    // Form toggle buttons
    if (this.toggleFormBtn) {
      this.toggleFormBtn.addEventListener('click', () => this.toggleForm());
    }
    
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener('click', () => this.hideForm());
    }
    
    // Form submission
    if (this.form) {
      this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }
    
    // Issue details expand/collapse
    document.querySelectorAll('.expand-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.toggleIssueDetails(e.target));
    });
    
    // Filters
    if (this.searchInput) {
      this.searchInput.addEventListener('input', () => {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => this.applyFilters(), 300);
      });
    }
    
    if (this.severityFilter) {
      this.severityFilter.addEventListener('change', () => this.applyFilters());
    }
    
    if (this.fileFilter) {
      this.fileFilter.addEventListener('change', () => this.applyFilters());
    }
  }
  
  toggleForm() {
    if (!this.requirementsForm) return;
    
    this.requirementsForm.classList.toggle('hidden');
    
    if (this.toggleFormBtn) {
      this.toggleFormBtn.textContent = this.requirementsForm.classList.contains('hidden') 
        ? 'Show Requirements' 
        : 'Hide Requirements';
    }
  }
  
  hideForm() {
    if (!this.requirementsForm) return;
    
    this.requirementsForm.classList.add('hidden');
    
    if (this.toggleFormBtn) {
      this.toggleFormBtn.textContent = 'Show Requirements';
    }
  }
  
  handleFormSubmit(e) {
    // Show loading state
    if (this.submitBtn) this.submitBtn.disabled = true;
    if (this.btnText) this.btnText.classList.add('hidden');
    if (this.btnLoading) this.btnLoading.classList.remove('hidden');
    
    // Show and animate progress bar
    if (this.analysisProgress) this.analysisProgress.classList.remove('hidden');
    if (this.progressStatus) this.progressStatus.textContent = 'Processing requirements...';
    
    // Simulate progress
    this.simulateProgress();
  }
  
  simulateProgress() {
    // Clear any existing interval
    if (this.progressInterval) {
      clearInterval(this.progressInterval);
    }
    
    let progress = 0;
    const statuses = [
      'Initializing analysis...',
      'Finding code files...',
      'Processing frontend code...',
      'Processing backend code...',
      'Analyzing requirements...',
      'Generating report...'
    ];
    
    this.progressInterval = setInterval(() => {
      // Increment progress
      progress += 1.5;
      
      // Update progress bar
      if (this.progressBar) {
        this.progressBar.style.width = Math.min(progress, 95) + '%';
      }
      
      // Update status message occasionally
      if (progress % 15 === 0 && this.progressStatus) {
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

// Initialize the analyzer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const analyzer = new RequirementsAnalyzer();
});