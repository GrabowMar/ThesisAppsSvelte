/**
 * AI Model Management Dashboard
 * Core JavaScript library using jQuery for dashboard functionality
 */

// Ensure jQuery is loaded before initializing
$(document).ready(function() {
  
  // Main App namespace to avoid global conflicts
  window.App = {
    // Configuration settings
    config: {
      autoRefresh: {
        enabled: false,
        interval: 30000,
        timer: null
      },
      api: {
        retryAttempts: 3,
        retryDelay: 1000
      },
      ui: {
        toastDuration: 3000
      }
    },
    
    // State management
    state: {
      isRefreshing: false,
      lastRefreshTime: null,
      pendingActions: new Map(),
      activeFilters: {}
    },
    
    // Initialize the application
    init: function() {
      console.log('Initializing AI Model Management Dashboard');
      this.Core.init();
      this.UI.init();
      this.setupGlobalListeners();
    },
    
    // Set up global event handlers
    setupGlobalListeners: function() {
      // Handle visibility change to manage auto-refresh
      $(document).on('visibilitychange', function() {
        if (document.hidden) {
          App.Core.autoRefresh.pause();
        } else {
          App.Core.autoRefresh.resume();
        }
      });
      
      // Set up global error handling
      $(window).on('error', App.Utils.handleGlobalError);
    }
  };

  // Core Module - Essential dashboard functionality
  App.Core = {
    init: function() {
      this.loadStoredSettings();
      this.autoRefresh.setup();
      this.systemInfo.init();
    },
    
    loadStoredSettings: function() {
      // Load settings from localStorage
      try {
        const storedSettings = localStorage.getItem('dashboardSettings');
        if (storedSettings) {
          const settings = JSON.parse(storedSettings);
          App.config.autoRefresh.enabled = settings.autoRefresh?.enabled ?? false;
        }
      } catch (e) {
        console.warn('Failed to load stored settings:', e);
      }
    },
    
    saveSettings: function() {
      try {
        const settings = {
          autoRefresh: {
            enabled: App.config.autoRefresh.enabled
          }
        };
        localStorage.setItem('dashboardSettings', JSON.stringify(settings));
      } catch (e) {
        console.warn('Failed to save settings:', e);
      }
    },
    
    // Auto-refresh functionality
    autoRefresh: {
      setup: function() {
        if (App.config.autoRefresh.enabled) {
          this.start();
        }
      },
      
      start: function() {
        if (App.config.autoRefresh.timer) return;
        
        App.config.autoRefresh.enabled = true;
        App.config.autoRefresh.timer = setInterval(function() {
          App.Core.refreshAllStatuses();
        }, App.config.autoRefresh.interval);
        
        App.Core.saveSettings();
        App.UI.updateAutoRefreshDisplay(true);
      },
      
      stop: function() {
        if (App.config.autoRefresh.timer) {
          clearInterval(App.config.autoRefresh.timer);
          App.config.autoRefresh.timer = null;
        }
        
        App.config.autoRefresh.enabled = false;
        App.Core.saveSettings();
        App.UI.updateAutoRefreshDisplay(false);
      },
      
      toggle: function() {
        if (App.config.autoRefresh.enabled) {
          this.stop();
        } else {
          this.start();
        }
      },
      
      pause: function() {
        if (App.config.autoRefresh.timer) {
          clearInterval(App.config.autoRefresh.timer);
          App.config.autoRefresh.timer = null;
          App.state.autoRefreshPaused = true;
        }
      },
      
      resume: function() {
        if (App.state.autoRefreshPaused && App.config.autoRefresh.enabled) {
          App.config.autoRefresh.timer = setInterval(function() {
            App.Core.refreshAllStatuses();
          }, App.config.autoRefresh.interval);
          App.state.autoRefreshPaused = false;
        }
      }
    },
    
    // Handle refreshing all app statuses
    refreshAllStatuses: function() {
      if (App.state.isRefreshing) return;
      
      App.state.isRefreshing = true;
      
      try {
        // Get all model sections
        $('[data-model-section]').each(function() {
          const model = $(this).data('model-section');
          if (!model) return;
          
          // Get all app cards for this model
          $(`[data-model="${model}"][data-app-id]`).each(function() {
            const appNum = $(this).data('app-id');
            if (!appNum) return;
            
            App.Core.updateAppStatus(model, appNum);
          });
        });
        
        // Update refresh timestamp
        App.state.lastRefreshTime = new Date();
        App.UI.updateRefreshTimestamp();
      } catch (error) {
        console.error('Error refreshing statuses:', error);
        App.Utils.logError({
          message: 'Failed to refresh all statuses',
          error
        });
      } finally {
        App.state.isRefreshing = false;
      }
    },
    
    // Update status for a specific app
    updateAppStatus: function(model, appNum) {
      if (!model || !appNum) return;
      
      return $.ajax({
        url: `/status/${model}/${appNum}`,
        method: 'GET',
        dataType: 'json',
        cache: false,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .done(function(data) {
        App.UI.updateStatusDisplay(model, appNum, data);
      })
      .fail(function(jqXHR, textStatus, errorThrown) {
        console.error(`Error updating status for ${model} app ${appNum}:`, errorThrown);
      });
    },
    
    // Perform an action on an app
    performAppAction: function(action, model, appNum) {
      if (!action || !model || !appNum) {
        return $.Deferred().reject('Missing required parameters for action');
      }
      
      // Show special handling for rebuild which may take longer
      if (action === 'rebuild') {
        App.UI.showToast(`Rebuilding ${model} App ${appNum}. This may take several minutes...`, 'info');
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
      .done(function(result) {
        if (result && result.message) {
          console.log(`${action} result:`, result.message);
        }
        return true;
      })
      .fail(function(jqXHR, textStatus, errorThrown) {
        console.error(`Action '${action}' failed:`, errorThrown);
        throw new Error(`Failed to ${action}: ${errorThrown}`);
      });
    },
    
    // Perform batch operation on multiple apps
    performBatchOperation: function(action, model) {
      if (!action || !model) {
        return $.Deferred().reject('Missing required parameters for batch operation');
      }
      
      const modelSection = $(`[data-model-section="${model}"]`);
      if (modelSection.length === 0) {
        return $.Deferred().reject(`Model section not found for ${model}`);
      }
      
      // Find all apps for this model
      const appCards = modelSection.find(`[data-model="${model}"][data-app-id]`);
      if (appCards.length === 0) {
        return $.Deferred().reject(`No apps found for model ${model}`);
      }
      
      // Get app numbers
      const appNumbers = $.map(appCards, function(card) {
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
        const processBatch = function() {
          const promises = batch.map(function(appNum) {
            return App.Core.processBatchOperation(action, model, appNum)
              .then(function(result) {
                processed++;
                if (result) success++;
                else failed++;
                
                // Update UI with progress
                App.UI.updateBatchProgress(model, action, processed, appNumbers.length);
                
                return result;
              });
          });
          
          return $.when.apply($, promises);
        };
        
        batchPromises.push(processBatch);
      }
      
      // Execute batches sequentially
      let chain = $.Deferred().resolve();
      batchPromises.forEach(function(batchFn) {
        chain = chain.then(batchFn);
      });
      
      // When all batches are done
      chain.then(function() {
        // Update final status
        App.UI.updateBatchResult(model, action, success, failed, appNumbers.length);
        
        // Refresh statuses
        setTimeout(function() {
          App.Core.refreshAllStatuses();
        }, 1000);
        
        deferred.resolve({ success, failed, total: appNumbers.length });
      }).fail(function(error) {
        console.error('Batch operation failed:', error);
        deferred.reject(error);
      });
      
      return deferred.promise();
    },
    
    // Process single batch operation
    processBatchOperation: function(action, model, appNum) {
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
        .then(function() {
          return true;
        })
        .fail(function() {
          return false;
        });
      }
      
      // Handle standard actions with retry logic
      return App.API.fetchWithRetry(`/${action}/${model}/${appNum}`)
        .then(function() {
          return true;
        })
        .fail(function() {
          return false;
        });
    },
    
    // Systems info handling
    systemInfo: {
      init: function() {
        this.load();
        // Refresh system info periodically (every 60s)
        setInterval($.proxy(this.load, this), 60000);
      },
      
      load: function() {
        $.ajax({
          url: '/api/system-info',
          method: 'GET',
          dataType: 'json',
          cache: false,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .done(function(data) {
          App.UI.updateSystemInfoDisplay(data);
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
          console.error('Failed to load system info:', errorThrown);
        });
      }
    }
  };

  // UI Module - Interface interactions
  App.UI = {
    // Element selector mapping for easier maintenance
    selectors: {
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
    },
    
    init: function() {
      this.setupEventListeners();
      this.setupFilters();
    },
    
    setupEventListeners: function() {
      // Action buttons
      $(this.selectors.actionButtons).each(function() {
        const $button = $(this);
        if (!$button.data('action')) return;
        
        $button.on('click', function(e) {
          App.UI.handleActionButton(e);
        });
      });
      
      // Refresh all button
      $(this.selectors.refreshAllBtn).on('click', function() {
        App.Core.refreshAllStatuses();
      });
      
      // Toggle auto-refresh button
      $(this.selectors.toggleAutorefreshBtn).on('click', function() {
        App.Core.autoRefresh.toggle();
      });
      
      // Batch menu buttons
      $(this.selectors.batchMenu).on('click', function(e) {
        e.stopPropagation();
        const dropdown = $(this).next(App.UI.selectors.batchMenuItems);
        
        dropdown.toggleClass('hidden');
        
        // Close other open dropdowns
        $(App.UI.selectors.batchMenuItems).not(dropdown).addClass('hidden');
      });
      
      // Close dropdowns when clicking elsewhere
      $(document).on('click', function() {
        $(App.UI.selectors.batchMenuItems).addClass('hidden');
      });
      
      // Batch action buttons
      $(this.selectors.batchAction).on('click', function(e) {
        App.UI.handleBatchAction(e);
      });
    },
    
    setupFilters: function() {
      const $searchInput = $(this.selectors.searchInput);
      const $modelFilter = $(this.selectors.modelFilter);
      const $statusFilter = $(this.selectors.statusFilter);
      
      if ($searchInput.length) {
        $searchInput.on('input', App.Utils.debounce(function() {
          App.UI.filterApps();
        }, 300));
      }
      
      if ($modelFilter.length) {
        $modelFilter.on('change', function() {
          App.UI.filterApps();
        });
      }
      
      if ($statusFilter.length) {
        $statusFilter.on('change', function() {
          App.UI.filterApps();
        });
      }
    },
    
    filterApps: function() {
      const $searchInput = $(this.selectors.searchInput);
      const $modelFilter = $(this.selectors.modelFilter);
      const $statusFilter = $(this.selectors.statusFilter);
      
      if (!$searchInput.length && !$modelFilter.length && !$statusFilter.length) return;
      
      const searchTerm = $searchInput.length ? $searchInput.val().toLowerCase() : '';
      const modelValue = $modelFilter.length ? $modelFilter.val() : 'all';
      const statusValue = $statusFilter.length ? $statusFilter.val() : 'all';
      
      // Update active filters
      App.state.activeFilters = {
        search: searchTerm,
        model: modelValue,
        status: statusValue
      };
      
      // Apply filters to app cards
      let visibleCount = 0;
      
      $(this.selectors.appCards).each(function() {
        const $card = $(this);
        const model = $card.data('model') || '';
        const appName = $card.data('app-name') || '';
        const appId = $card.data('app-id') || '';
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
    },
    
    toggleNoResultsMessage: function(show) {
      $(this.selectors.noResultsMessage).toggle(show);
    },
    
    handleActionButton: function(event) {
      const $button = $(event.currentTarget);
      const action = $button.data('action');
      const model = $button.data('model');
      const appNum = $button.data('app-num');
      
      if (!action || !model || !appNum) {
        console.error('Missing required data attributes on button', $button);
        this.showToast('Invalid button configuration', 'error');
        return;
      }
      
      // Prevent duplicate actions
      const actionKey = `${action}-${model}-${appNum}`;
      if (App.state.pendingActions.has(actionKey)) {
        console.log(`Action ${actionKey} already in progress, skipping`);
        return;
      }
      
      // Add to pending actions
      const originalText = $button.text();
      App.state.pendingActions.set(actionKey, true);
      
      // Update button state
      $button.prop('disabled', true);
      $button.html(this.getLoadingIndicator(action));
      
      // Perform the action
      App.Core.performAppAction(action, model, appNum)
        .then(function() {
          // Update app status after action
          return App.Core.updateAppStatus(model, appNum);
        })
        .then(function() {
          // Show success message
          App.UI.showToast(`${App.Utils.capitalizeFirst(action)} operation successful`);
        })
        .fail(function(error) {
          App.UI.showToast(`Failed to ${action}: ${error.message || error}`, 'error');
          App.Utils.logError({
            message: `Action '${action}' failed`,
            context: { action, model, appNum },
            error
          });
        })
        .always(function() {
          // Restore button state
          $button.prop('disabled', false);
          $button.text(originalText);
          
          // Remove from pending actions
          App.state.pendingActions.delete(actionKey);
        });
    },
    
    handleBatchAction: function(event) {
      const $button = $(event.currentTarget);
      const action = $button.data('action');
      const model = $button.data('model');
      
      if (!action || !model) {
        console.error('Missing required data attributes on batch button', $button);
        this.showToast('Invalid batch button configuration', 'error');
        return;
      }
      
      // Close the dropdown menu
      $button.closest(this.selectors.batchMenuItems).addClass('hidden');
      
      // Confirm the batch operation
      if (!confirm(`Are you sure you want to ${action} all apps for model ${model}?`)) {
        return;
      }
      
      // Show batch operation starting
      this.showBatchStatus(model, action, 'starting');
      
      // Perform batch operation
      App.Core.performBatchOperation(action, model)
        .done(function(result) {
          // Show success message
          if (result.failed === 0) {
            App.UI.showToast(`All ${model} apps ${action}ed successfully`);
          } else if (result.success === 0) {
            App.UI.showToast(`Failed to ${action} any ${model} apps`, 'error');
          } else {
            App.UI.showToast(`${result.success} succeeded, ${result.failed} failed`, 'warning');
          }
        })
        .fail(function(error) {
          App.UI.showToast(`Batch operation failed: ${error.message || error}`, 'error');
          App.UI.showBatchStatus(model, action, 'failed');
          
          App.Utils.logError({
            message: `Batch operation '${action}' failed`,
            context: { action, model },
            error
          });
        });
    },
    
    updateStatusDisplay: function(model, appNum, data) {
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
    },
    
    updateMetricsDisplay: function($card, metrics) {
      if (!$card || !metrics) return;
      
      // CPU usage
      const $cpuEl = $card.find('.metric-cpu');
      if ($cpuEl.length && metrics.cpu_percent !== undefined) {
        $cpuEl.text(`${metrics.cpu_percent.toFixed(1)}%`);
      }
      
      // Memory usage
      const $memEl = $card.find('.metric-memory');
      if ($memEl.length && metrics.memory_usage !== undefined) {
        $memEl.text(App.Utils.formatBytes(metrics.memory_usage));
      }
      
      // Request count
      const $requestsEl = $card.find('.metric-requests');
      if ($requestsEl.length && metrics.request_count !== undefined) {
        $requestsEl.text(metrics.request_count.toLocaleString());
      }
    },
    
    showBatchStatus: function(model, action, state = 'starting') {
      const $modelSection = $(`[data-model-section="${model}"]`);
      if ($modelSection.length === 0) return;
      
      const $statusEl = $modelSection.find('.batch-status');
      const $statusTextEl = $statusEl.find('.batch-status-text');
      
      if (!$statusEl.length || !$statusTextEl.length) return;
      
      // Show status element
      $statusEl.removeClass('hidden');
      
      // Set text based on state
      if (state === 'starting') {
        $statusTextEl.text(`${App.Utils.capitalizeFirst(action)}ing apps...`);
      } else if (state === 'failed') {
        $statusTextEl.text(`Failed to ${action} apps`);
        $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-red-100 text-red-800 border border-red-300 rounded-sm');
      }
    },
    
    updateBatchProgress: function(model, action, completed, total) {
      const $progressEl = $(`[data-model-section="${model}"] .batch-progress`);
      if ($progressEl.length) {
        $progressEl.text(`${completed}/${total}`);
      }
    },
    
    updateBatchResult: function(model, action, success, failed, total) {
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
        setTimeout(function() {
          $statusEl.addClass('hidden');
        }, 5000);
      } else if (success === 0) {
        $statusTextEl.text(`Failed to ${action} all apps`);
        $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-red-100 text-red-800 border border-red-300 rounded-sm');
      } else {
        $statusTextEl.text(`${success} succeeded, ${failed} failed`);
        $statusEl.find('span').attr('class', 'px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 border border-yellow-300 rounded-sm');
      }
    },
    
    updateSystemInfoDisplay: function(data) {
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
        $uptimeEl.text(App.Utils.formatUptime(data.uptime_seconds));
      }
    },
    
    updateRefreshTimestamp: function() {
      if (!App.state.lastRefreshTime) return;
      
      const $timestampEl = $(this.selectors.lastRefreshTime);
      if ($timestampEl.length) {
        $timestampEl.text(App.state.lastRefreshTime.toLocaleTimeString());
      }
    },
    
    updateAutoRefreshDisplay: function(enabled) {
      const $toggleBtn = $(this.selectors.toggleAutorefreshBtn);
      const $statusText = $(this.selectors.autorefreshText);
      
      if ($toggleBtn.length) {
        $toggleBtn.text(enabled ? 'Disable Auto-Refresh' : 'Enable Auto-Refresh');
      }
      
      if ($statusText.length) {
        $statusText.text(enabled 
          ? `Auto Refresh: On (${App.config.autoRefresh.interval/1000}s)` 
          : 'Auto Refresh: Off');
      }
    },
    
    getLoadingIndicator: function(action) {
      return `<svg class="inline-block w-4 h-4 mr-1 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>${App.Utils.capitalizeFirst(action)}ing...`;
    },
    
    showToast: function(message, type = 'success') {
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
      setTimeout(function() {
        $toast.css('opacity', 0);
        setTimeout(function() {
          $toast.remove();
        }, 300);
      }, App.config.ui.toastDuration);
      
      return $toast;
    }
  };

  // API Module - Network requests and data handling
  App.API = {
    fetchWithRetry: function(url, options = {}, retries = App.config.api.retryAttempts) {
      // Default headers
      const headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache'
      };
      
      // Default request options
      const ajaxOptions = $.extend({
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
      const attemptRequest = function(remainingRetries) {
        return $.ajax(ajaxOptions)
          .fail(function(jqXHR, textStatus, errorThrown) {
            if (remainingRetries <= 0) {
              return $.Deferred().reject(errorThrown || textStatus);
            }
            
            console.warn(`API request attempt failed (${retries - remainingRetries + 1}/${retries}):`, textStatus);
            
            // Wait before retry using exponential backoff
            const delay = App.config.api.retryDelay * Math.pow(2, retries - remainingRetries);
            
            return new Promise(resolve => setTimeout(resolve, delay))
              .then(function() {
                return attemptRequest(remainingRetries - 1);
              });
          });
      };
      
      return attemptRequest(retries);
    }
  };

  // Utils Module - Helper functions
  App.Utils = {
    debounce: function(func, wait) {
      let timeout;
      return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
          func.apply(context, args);
        }, wait);
      };
    },
    
    capitalizeFirst: function(string) {
      if (!string) return '';
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    
    formatBytes: function(bytes) {
      if (bytes === 0) return '0 B';
      
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    formatUptime: function(seconds) {
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
    },
    
    handleGlobalError: function(event) {
      const errorDetails = {
        message: event.originalEvent.message || 'Unknown error',
        filename: event.originalEvent.filename,
        lineno: event.originalEvent.lineno,
        colno: event.originalEvent.colno,
        stack: event.originalEvent.error ? event.originalEvent.error.stack : 'No stack trace',
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
      .fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Failed to send error to server:', errorThrown);
      });
      
      return true; // Prevent default error handling
    },
    
    logError: function(errorData) {
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
      .fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Failed to send error to server:', errorThrown);
      });
    }
  };

  // Features Module - Add-on functionality for specific pages
  App.Features = {
    // Security analysis related functionality
    securityAnalysis: {
      init: function() {
        this.setupEventListeners();
        this.loadSecuritySummary();
      },
      
      setupEventListeners: function() {
        // Setup security scan buttons
        $('.security-scan-btn').on('click', $.proxy(this.handleScanClick, this));
        
        // Setup modal close buttons
        $('.modal-close').on('click', function() {
          $('#securityModal').addClass('hidden');
        });
        
        // Setup start analysis button
        $('#startAnalysis').on('click', $.proxy(this.startAnalysis, this));
      },
      
      handleScanClick: function(event) {
        const $btn = $(event.currentTarget);
        const model = $btn.data('model');
        const appNum = $btn.data('app-num');
        
        if (!model || !appNum) {
          console.error('Missing required data attributes on security scan button');
          return;
        }
        
        // Store current analysis context
        App.state.currentAnalysis = { model, appNum };
        
        // Show modal
        $('#securityModal').removeClass('hidden');
      },
      
      startAnalysis: function() {
        if (!App.state.currentAnalysis) return;
        
        const { model, appNum } = App.state.currentAnalysis;
        const analysisType = $('#analysisType').val() || 'full';
        const aiModel = $('#aiModel').val() || 'default';
        
        // Show loading state
        $('#scanResults').addClass('hidden');
        $('#scanLoading').removeClass('hidden');
        $('#startAnalysis').prop('disabled', true);
        
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
        .done($.proxy(function(results) {
          // Update results display
          if (results) {
            $('#modalHighCount').text(results.counts?.high || 0);
            $('#modalMediumCount').text(results.counts?.medium || 0);
            $('#modalLowCount').text(results.counts?.low || 0);
            $('#summaryDetails').text(results.summary || 'No issues found');
            $('#aiAnalysis').text(results.ai_analysis || 'No analysis available');
            
            // Update app UI with results
            this.updateSecurityBadges(model, appNum, results);
          }
          
          // Show results
          $('#scanLoading').addClass('hidden');
          $('#scanResults').removeClass('hidden');
        }, this))
        .fail(function(jqXHR, textStatus, errorThrown) {
          App.UI.showToast(`Analysis failed: ${errorThrown}`, 'error');
          $('#scanLoading').addClass('hidden');
          
          App.Utils.logError({
            message: 'Security analysis failed',
            context: { model, appNum, analysisType, aiModel },
            error: errorThrown
          });
        })
        .always(function() {
          $('#startAnalysis').prop('disabled', false);
        });
      },
      
      updateSecurityBadges: function(model, appNum, results) {
        const $appCard = $(`[data-model="${model}"][data-app-id="${appNum}"]`);
        if (!$appCard.length) return;
        
        const $indicator = $appCard.find('.security-indicator');
        if (!$indicator.length) return;
        
        if (results.total_issues > 0) {
          // Determine severity level
          const securityLevel = results.counts.high > 0 ? 'high' :
                              results.counts.medium > 0 ? 'medium' : 'low';
          
          // Update indicator
          $indicator.removeClass('hidden');
          $indicator.attr('class', `security-indicator text-xs px-1 rounded ${
            securityLevel === 'high' ? 'bg-red-100 text-red-800' :
            securityLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-blue-100 text-blue-800'
          }`);
          
          $indicator.text(`${results.total_issues} ${
            securityLevel === 'high' ? 'High' :
            securityLevel === 'medium' ? 'Med' : 'Low'
          }`);
        } else {
          $indicator.addClass('hidden');
        }
      },
      
      loadSecuritySummary: function() {
        $.ajax({
          url: '/api/security/global-summary',
          method: 'GET',
          dataType: 'json'
        })
        .done(function(data) {
          // Update global counters
          $('#totalHighIssues').text(data.totals?.high || 0);
          $('#totalMediumIssues').text(data.totals?.medium || 0);
          $('#totalLowIssues').text(data.totals?.low || 0);
          $('#lastGlobalScan').text(data.last_scan 
            ? new Date(data.last_scan).toLocaleString() 
            : 'Never');
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
          console.error('Failed to load security summary:', errorThrown);
        });
      }
    },
    
    // Performance test related functionality
    performanceTest: {
      init: function() {
        this.setupEventListeners();
      },
      
      setupEventListeners: function() {
        $('#runTest').on('click', $.proxy(this.runTest, this));
        $('#stopTest').on('click', $.proxy(this.stopTest, this));
        $('#clearLog').on('click', function() {
          $('#outputLog').text('');
        });
      },
      
      runTest: function() {
        const numUsers = parseInt($('#numUsers').val()) || 10;
        const duration = parseInt($('#duration').val()) || 30;
        const spawnRate = parseInt($('#spawnRate').val()) || 1;
        
        // Update UI for test start
        $('#runTest').prop('disabled', true);
        $('#stopTest').removeClass('hidden');
        $('#testStatus').text('Running...');
        $('#scanProgress').removeClass('hidden');
        
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
        .done($.proxy(function(result) {
          if (result.status === 'success') {
            // Update progress to 100%
            $('#progressBar').css('width', '100%');
            
            // Update results display
            this.updateStatistics(result.data);
            this.appendToLog('Test completed successfully');
            
            // Show download button if report available
            if (result.report_path) {
              $('#downloadReport').removeClass('hidden');
            }
          } else {
            throw new Error(result.error || 'Test failed');
          }
        }, this))
        .fail($.proxy(function(jqXHR, textStatus, errorThrown) {
          $('#progressBar').css('width', '0%');
          $('#testStatus').text('Failed');
          this.appendToLog(`Error: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
          App.UI.showToast(`Test failed: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`, 'error');
        }, this))
        .always(function() {
          $('#runTest').prop('disabled', false);
          $('#stopTest').addClass('hidden');
        });
      },
      
      stopTest: function() {
        this.appendToLog('Stopping test...');
        
        $.ajax({
          url: `${window.location.href}/stop`,
          method: 'POST'
        })
        .done($.proxy(function() {
          this.appendToLog('Test stopped successfully');
          $('#testStatus').text('Stopped');
        }, this))
        .fail($.proxy(function(jqXHR, textStatus, errorThrown) {
          this.appendToLog(`Failed to stop test: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
        }, this))
        .always(function() {
          $('#runTest').prop('disabled', false);
          $('#stopTest').addClass('hidden');
        });
      },
      
      simulateProgress: function(duration) {
        let elapsed = 0;
        const interval = 1000; // Update every second
        $('#progressBar').css('width', '0%');
        
        const timer = setInterval(function() {
          elapsed += interval;
          const percentage = Math.min(Math.floor((elapsed / (duration * 1000)) * 100), 95);
          $('#progressBar').css('width', `${percentage}%`);
          
          if (elapsed >= duration * 1000) {
            clearInterval(timer);
          }
        }, interval);
      },
      
      updateStatistics: function(data) {
        if (!data) return;
        
        // Update basic statistics
        $('#totalRequests').text(data.total_requests || 0);
        $('#totalFailures').text(data.total_failures || 0);
        $('#requestsPerSec').text(data.requests_per_sec ? data.requests_per_sec.toFixed(2) : 0);
        $('#avgResponseTime').text(data.avg_response_time ? data.avg_response_time.toFixed(2) + ' ms' : '-');
        $('#medianResponseTime').text(data.median_response_time ? data.median_response_time.toFixed(2) + ' ms' : '-');
        $('#percentile95').text(data.percentile_95 ? data.percentile_95.toFixed(2) + ' ms' : '-');
        $('#percentile99').text(data.percentile_99 ? data.percentile_99.toFixed(2) + ' ms' : '-');
        $('#lastRun').text(data.start_time || 'Never');
        $('#testStatus').text('Completed');
        
        // Update endpoint table
        this.updateEndpointTable(data.endpoints || []);
        
        // Update error table
        this.updateErrorTable(data.errors || []);
        
        // Show/hide visualization
        $('#visualizationSection').toggleClass('hidden', !(data.endpoints && data.endpoints.length > 0));
      },
      
      updateEndpointTable: function(endpoints) {
        const $tableBody = $('#endpointTableBody');
        if (!$tableBody.length) return;
        
        $tableBody.empty();
        
        if (endpoints && endpoints.length > 0) {
          endpoints.forEach(function(endpoint) {
            const $row = $('<tr>');
            $row.html(`
              <td class="border border-gray-300 px-2 py-1 text-xs">${endpoint.name || ''}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs">${endpoint.method || ''}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${endpoint.num_requests || 0}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${endpoint.num_failures || 0}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.median_response_time || 0).toFixed(2)}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.avg_response_time || 0).toFixed(2)}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.min_response_time || 0).toFixed(2)}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.max_response_time || 0).toFixed(2)}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${(endpoint.current_rps || 0).toFixed(2)}</td>
            `);
            $tableBody.append($row);
          });
        } else {
          const $row = $('<tr>');
          $row.html(`<td colspan="9" class="border border-gray-300 px-2 py-1 text-xs text-center">No endpoint data available</td>`);
          $tableBody.append($row);
        }
      },
      
      updateErrorTable: function(errors) {
        const $errorSection = $('#errorSection');
        const $errorTable = $('#errorTableBody');
        
        if (!$errorSection.length || !$errorTable.length) return;
        
        $errorTable.empty();
        
        if (errors && errors.length > 0) {
          $errorSection.removeClass('hidden');
          
          errors.forEach(function(error) {
            const $row = $('<tr>');
            $row.html(`
              <td class="border border-gray-300 px-2 py-1 text-xs text-red-600">${error.error_type || 'Unknown'}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs text-right">${error.count || 0}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs">${error.endpoint || ''}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs">${error.method || ''}</td>
              <td class="border border-gray-300 px-2 py-1 text-xs">${error.description || ''}</td>
            `);
            $errorTable.append($row);
          });
        } else {
          $errorSection.addClass('hidden');
        }
      },
      
      appendToLog: function(message) {
        const outputLog = $('#outputLog');
        if (!outputLog.length) return;
        
        const timestamp = new Date().toLocaleTimeString();
        outputLog.append(`[${timestamp}] ${message}\n`);
        outputLog.scrollTop(outputLog[0].scrollHeight);
      }
    },
    
    // Requirements analysis functionality
    requirementsAnalysis: {
      init: function() {
        this.setupEventListeners();
        this.setupForm();
      },
      
      setupEventListeners: function() {
        // Toggle requirement details
        $('.hover\\:bg-gray-50').on('click', function() {
          const detailId = $(this).attr('onclick')?.match(/toggleDetails\('([^']+)'\)/)?.[1];
          if (detailId) {
            $(`#${detailId}`).toggle();
          }
        });
      },
      
      setupForm: function() {
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
    },
    
    // Security analysis page functionality
    securityAnalysisPage: {
      init: function() {
        this.setupFilters();
        this.setupExpandButtons();
      },
      
      setupFilters: function() {
        const applyFilters = function() {
          const searchTerm = $('#searchIssues').val()?.toLowerCase() || '';
          const selectedRisk = $('#riskFilter').val() || 'all';
          const selectedConfidence = $('#confidenceFilter').val() || 'all';
          
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
        $('#searchIssues').on('input', App.Utils.debounce(applyFilters, 300));
        $('#riskFilter, #confidenceFilter').on('change', applyFilters);
        
        // Initial filter application
        applyFilters();
      },
      
      setupExpandButtons: function() {
        $('.expand-btn').on('click', function() {
          const $details = $(this).closest('div').next().find('.alert-details');
          $details.toggleClass('hidden');
          $(this).text($details.hasClass('hidden') ? 'Expand' : 'Collapse');
        });
      }
    },
    
    // ZAP scan page functionality
    zapScan: {
      init: function() {
        this.setupEventListeners();
        this.updateTargetUrl();
      },
      
      setupEventListeners: function() {
        $('#startScan').on('click', $.proxy(this.startScan, this));
        $('#stopScan').on('click', $.proxy(this.stopScan, this));
        $('#clearLog').on('click', function() {
          $('#progressLog').text('');
        });
      },
      
      updateTargetUrl: function() {
        // Extract model and app from URL
        const urlParts = window.location.pathname.split('/');
        const model = urlParts[urlParts.length - 2] || '';
        const appNum = urlParts[urlParts.length - 1] || '';
        
        // Calculate port using the logic from the original code
        const port = this.calculatePort(model, parseInt(appNum));
        
        $('#targetUrl').text(`http://localhost:${port}`);
      },
      
      calculatePort: function(model, appNum) {
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
      },
      
      startScan: function() {
        // Get model and app from URL
        const urlParts = window.location.pathname.split('/');
        const model = urlParts[urlParts.length - 2] || '';
        const appNum = urlParts[urlParts.length - 1] || '';
        
        // Get scan options
        const scanOptions = {
          spiderDepth: parseInt($('#spiderDepth').val()) || 5,
          threadCount: parseInt($('#threadCount').val()) || 2,
          useAjaxSpider: $('#ajaxSpider').is(':checked') || false,
          usePassiveScan: $('#passiveScan').is(':checked') || true,
          useActiveScan: $('#activeScan').is(':checked') || true,
          scanPolicy: $('#scanPolicy').val() || 'Default Policy'
        };
        
        // Update UI for scan start
        $('#startScan').prop('disabled', true);
        $('#stopScan').removeClass('hidden');
        $('#scanStatus').text('Starting...');
        $('#scanProgress').removeClass('hidden');
        
        this.appendToLog(`Starting scan with options: Spider Depth=${scanOptions.spiderDepth}, Threads=${scanOptions.threadCount}, AJAX=${scanOptions.useAjaxSpider}`);
        
        // Start the scan
        $.ajax({
          url: `/zap/scan/${model}/${appNum}`,
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify(scanOptions)
        })
        .done($.proxy(function() {
          this.appendToLog('Scan started successfully');
          this.pollProgress(model, appNum);
        }, this))
        .fail($.proxy(function(jqXHR, textStatus, errorThrown) {
          this.appendToLog(`Error: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
          $('#scanStatus').text('Error');
          $('#startScan').prop('disabled', false);
          $('#stopScan').addClass('hidden');
          App.UI.showToast(`Failed to start scan: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`, 'error');
        }, this));
      },
      
      stopScan: function() {
        // Get model and app from URL
        const urlParts = window.location.pathname.split('/');
        const model = urlParts[urlParts.length - 2] || '';
        const appNum = urlParts[urlParts.length - 1] || '';
        
        this.appendToLog('Stopping scan...');
        
        $.ajax({
          url: `/zap/scan/${model}/${appNum}/stop`,
          method: 'POST'
        })
        .done($.proxy(function() {
          this.appendToLog('Scan stopped successfully');
          $('#scanStatus').text('Stopped');
          $('#startScan').prop('disabled', false);
          $('#stopScan').addClass('hidden');
        }, this))
        .fail($.proxy(function(jqXHR, textStatus, errorThrown) {
          this.appendToLog(`Error stopping scan: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`);
          App.UI.showToast(`Failed to stop scan: ${errorThrown || jqXHR.responseJSON?.error || textStatus}`, 'error');
        }, this));
      },
      
      pollProgress: function(model, appNum) {
        let pollingActive = true;
        let pollingErrorCount = 0;
        
        const updateUI = $.proxy(function() {
          $.ajax({
            url: `/zap/scan/${model}/${appNum}/status`,
            method: 'GET',
            dataType: 'json'
          })
          .done($.proxy(function(data) {
            // Update progress bar
            $('#progressBar').css('width', `${Math.min(Math.max(data.progress, 0), 100)}%`);
            
            // Update status text
            $('#scanStatus').text(data.status || 'Unknown');
            
            // Update count elements
            $('#highCount').text(data.high_count || 0);
            $('#mediumCount').text(data.medium_count || 0);
            $('#lowCount').text(data.low_count || 0);
            $('#infoCount').text(data.info_count || 0);
            
            // Log important state changes
            if (data.status !== 'Running' && data.status !== 'Starting') {
              this.appendToLog(`Status changed to: ${data.status}`);
            }
            
            // Check if scan is complete
            if (data.status === 'Complete') {
              pollingActive = false;
              
              $('#stopScan').addClass('hidden');
              $('#startScan').prop('disabled', false);
              $('#lastScanTime').text(new Date().toLocaleString());
              
              this.appendToLog('Scan completed. Reloading page to show results...');
              setTimeout(function() {
                window.location.reload();
              }, 1000);
              return;
            }
            
            // Continue polling if still active
            if (pollingActive) {
              setTimeout(updateUI, 2000);
            }
          }, this))
          .fail($.proxy(function(jqXHR, textStatus, errorThrown) {
            console.error('Polling error:', errorThrown);
            this.appendToLog(`Error updating status: ${errorThrown || textStatus}`);
            
            // Increment error count
            pollingErrorCount++;
            
            // Stop polling after too many errors
            if (pollingErrorCount >= 3) {
              pollingActive = false;
              this.appendToLog('Stopped polling due to repeated errors');
              return;
            }
            
            // Retry with longer delay on error
            if (pollingActive) {
              setTimeout(updateUI, 5000);
            }
          }, this));
        }, this);
        
        // Start the polling loop
        updateUI();
      },
      
      appendToLog: function(message) {
        const $progressLog = $('#progressLog');
        if (!$progressLog.length) return;
        
        const timestamp = new Date().toLocaleTimeString();
        $progressLog.append(`[${timestamp}] ${message}\n`);
        $progressLog.scrollTop($progressLog[0].scrollHeight);
      }
    }
  };

  // Initialize application
  App.init();
});