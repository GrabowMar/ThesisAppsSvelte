// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function () {
   const dashboard = new DashboardController();
   dashboard.init();
});

class DashboardController {
   constructor() {
       this.autoRefreshInterval = null;
       this.autoRefreshDuration = 30000;
   }

   init() {
       this.initializeEventListeners();
       this.setupAutoRefresh();
       this.setupFilters();
       this.updateSystemInfo();
   }

   initializeEventListeners() {
       document.querySelectorAll('.action-btn').forEach(button => {
           button.addEventListener('click', (e) => this.handleAction(e));
       });

       const refreshBtn = document.getElementById('refreshAll');
       if (refreshBtn) {
           refreshBtn.addEventListener('click', () => this.refreshAllStatuses());
       }

       const autoRefreshBtn = document.getElementById('toggleAutorefresh');
       if (autoRefreshBtn) {
           autoRefreshBtn.addEventListener('click', () => this.toggleAutoRefresh());
       }

       document.querySelectorAll('[data-quick-action]').forEach(button => {
           button.addEventListener('click', (e) => this.handleQuickAction(e));
       });
   }

   async handleAction(event) {
       const button = event.currentTarget;
       const { action, model, appNum } = button.dataset;
       const originalText = button.textContent;

       try {
           button.disabled = true;
           button.innerHTML = this.getLoadingSpinner(action);

           const response = await fetch(`/${action}/${model}/${appNum}`, {
               headers: { 'X-Requested-With': 'XMLHttpRequest' }
           });

           if (!response.ok) throw new Error(`Action failed: ${response.statusText}`);

           await this.updateAppStatus(model, appNum);
           this.showToast(`${action} completed successfully`);
       } catch (error) {
           console.error(error);
           this.showToast(error.message, 'error');
       } finally {
           button.disabled = false;
           button.textContent = originalText;
       }
   }

   async handleQuickAction(event) {
       const button = event.currentTarget;
       const action = button.dataset.quickAction;
       
       try {
           button.disabled = true;
           const response = await fetch(`/api/quick-action/${action}`, {
               method: 'POST',
               headers: { 'X-Requested-With': 'XMLHttpRequest' }
           });

           if (!response.ok) throw new Error('Action failed');
           
           await this.refreshAllStatuses();
           this.showToast(`${action} completed`);
       } catch (error) {
           this.showToast(error.message, 'error');
       } finally {
           button.disabled = false;
       }
   }

   async updateAppStatus(model, appNum) {
       try {
           const response = await fetch(`/api/container/${model}/${appNum}/status`);
           if (!response.ok) throw new Error('Failed to fetch status');

           const data = await response.json();
           const appCard = document.querySelector(`[data-app-id="${appNum}"][data-model="${model}"]`);
           if (appCard) this.updateStatusUI(appCard, data);
       } catch (error) {
           console.error('Status update failed:', error);
       }
   }

   updateStatusUI(appCard, status) {
       const backendStatus = appCard.querySelector('[data-status="backend"]');
       const frontendStatus = appCard.querySelector('[data-status="frontend"]');
       const statusBadge = appCard.querySelector('.status-badge');

       if (backendStatus) {
           backendStatus.textContent = status.backend.running ? 'Running' : 'Stopped';
           backendStatus.className = `font-medium ${status.backend.running ? 'text-green-700' : 'text-red-700'}`;
       }

       if (frontendStatus) {
           frontendStatus.textContent = status.frontend.running ? 'Running' : 'Stopped';
           frontendStatus.className = `font-medium ${status.frontend.running ? 'text-green-700' : 'text-red-700'}`;
       }

       const isRunning = status.backend.running && status.frontend.running;
       const isPartial = status.backend.running || status.frontend.running;

       if (statusBadge) {
           statusBadge.className = `status-badge text-xs px-2 py-0.5 border ${
               isRunning ? 'bg-green-100 text-green-800 border-green-700' :
               isPartial ? 'bg-yellow-100 text-yellow-800 border-yellow-700' :
               'bg-red-100 text-red-800 border-red-700'
           }`;
           statusBadge.textContent = isRunning ? 'Running' : isPartial ? 'Partial' : 'Stopped';
       }
   }

   async refreshAllStatuses() {
       const refreshBtn = document.getElementById('refreshAll');
       const originalText = refreshBtn.textContent;

       try {
           refreshBtn.disabled = true;
           refreshBtn.innerHTML = this.getLoadingSpinner();

           const apps = document.querySelectorAll('[data-app-id]');
           await Promise.all([...apps].map(app => 
               this.updateAppStatus(app.dataset.model, app.dataset.appId)
           ));

           this.updateSystemInfo();
           this.showToast('All statuses refreshed');
       } catch (error) {
           this.showToast('Failed to refresh statuses', 'error');
       } finally {
           refreshBtn.disabled = false;
           refreshBtn.textContent = originalText;
       }
   }

   setupFilters() {
       const searchInput = document.getElementById('searchApps');
       const modelFilter = document.getElementById('filterModel');
       const statusFilter = document.getElementById('filterStatus');

       const applyFilters = () => {
           const searchTerm = searchInput?.value.toLowerCase() || '';
           const modelValue = modelFilter?.value || '';
           const statusValue = statusFilter?.value || '';

           document.querySelectorAll('[data-app-id]').forEach(app => {
               const matchesSearch = app.textContent.toLowerCase().includes(searchTerm);
               const matchesModel = !modelValue || app.dataset.model === modelValue;
               const matchesStatus = !statusValue || this.getAppStatus(app) === statusValue;
               
               app.style.display = (matchesSearch && matchesModel && matchesStatus) ? '' : 'none';
           });

           this.updateModelSections();
       };

       [searchInput, modelFilter, statusFilter].forEach(filter => {
           filter?.addEventListener('change', applyFilters);
       });

       if (searchInput) {
           searchInput.addEventListener('input', this.debounce(applyFilters, 300));
       }
   }

   updateSystemInfo() {
       const healthStatus = document.querySelector('[data-health-status]');
       const dockerStatus = document.querySelector('[data-docker-status]'); 
       const lastUpdate = document.querySelector('[data-last-update]');

       if (healthStatus) healthStatus.textContent = 'Healthy';
       if (dockerStatus) dockerStatus.textContent = 'Connected';
       if (lastUpdate) lastUpdate.textContent = new Date().toLocaleString();
   }

   setupAutoRefresh() {
       const button = document.getElementById('toggleAutorefresh');
       if (button && button.dataset.enabled === 'true') {
           this.startAutoRefresh();
       }
   }

   toggleAutoRefresh() {
       const button = document.getElementById('toggleAutorefresh');
       const textSpan = button.querySelector('#autorefreshText');
       const isEnabled = button.dataset.enabled === 'true';

       if (isEnabled) {
           this.stopAutoRefresh();
           button.dataset.enabled = 'false';
           textSpan.textContent = 'Auto Refresh: Off';
       } else {
           this.startAutoRefresh();
           button.dataset.enabled = 'true';
           textSpan.textContent = 'Auto Refresh: On';
       }
   }

   startAutoRefresh() {
       this.refreshAllStatuses();
       this.autoRefreshInterval = setInterval(() => {
           this.refreshAllStatuses();
       }, this.autoRefreshDuration);
   }

   stopAutoRefresh() {
       if (this.autoRefreshInterval) {
           clearInterval(this.autoRefreshInterval);
           this.autoRefreshInterval = null;
       }
   }

   showToast(message, type = 'success') {
       const toast = document.createElement('div');
       toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white
           ${type === 'error' ? 'bg-red-500' : 'bg-green-500'}`;
       toast.textContent = message;
       document.body.appendChild(toast);
       setTimeout(() => toast.remove(), 3000);
   }

   getLoadingSpinner(action = 'Working') {
       return `<svg class="w-3 h-3 animate-spin mr-1 inline" viewBox="0 0 24 24">
           <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
           <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
       </svg>${action}...`;
   }

   getAppStatus(app) {
       const status = app.querySelector('.status-badge')?.textContent.toLowerCase();
       return status || '';
   }

   updateModelSections() {
       document.querySelectorAll('[data-model-section]').forEach(section => {
           const hasVisibleApps = [...section.querySelectorAll('[data-app-id]')]
               .some(app => app.style.display !== 'none');
           section.style.display = hasVisibleApps ? '' : 'none';
       });

       const noResults = document.getElementById('noResultsMessage');
       if (noResults) {
           const hasAnyVisible = document.querySelector('[data-app-id]:not([style*="display: none"])');
           noResults.classList.toggle('hidden', hasAnyVisible);
       }
   }

   debounce(func, wait) {
       let timeout;
       return (...args) => {
           clearTimeout(timeout);
           timeout = setTimeout(() => func.apply(this, args), wait);
       };
   }
}