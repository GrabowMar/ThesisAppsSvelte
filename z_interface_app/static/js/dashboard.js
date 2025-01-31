// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Initialize controllers
    const dashboard = new DashboardController();
    dashboard.init();
});

class DashboardController {
    constructor() {
        this.autoRefreshInterval = null;
        this.autoRefreshDuration = 30000; // 30 seconds
    }

    init() {
        this.initializeEventListeners();
        this.setupAutoRefresh();
        this.setupFilters();
    }

    initializeEventListeners() {
        // Action buttons
        document.querySelectorAll('.action-btn').forEach(button => {
            button.addEventListener('click', (e) => this.handleAction(e));
        });

        // Batch actions
        document.querySelectorAll('.batch-action').forEach(button => {
            button.addEventListener('click', (e) => this.handleBatchAction(e));
        });

        // Select all buttons
        document.querySelectorAll('.select-all-btn').forEach(button => {
            button.addEventListener('click', (e) => this.handleSelectAll(e));
        });

        // Refresh button
        const refreshBtn = document.getElementById('refreshAll');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAllStatuses());
        }

        // Auto-refresh toggle
        const autoRefreshBtn = document.getElementById('toggleAutorefresh');
        if (autoRefreshBtn) {
            autoRefreshBtn.addEventListener('click', () => this.toggleAutoRefresh());
        }
    }

    async handleAction(event) {
        const button = event.currentTarget;
        const { action, model, appNum } = button.dataset;
        const originalText = button.innerHTML;

        try {
            button.disabled = true;
            button.innerHTML = this.getLoadingText(action);

            const response = await fetch(`/${action}/${model}/${appNum}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) {
                throw new Error(`Action failed: ${response.statusText}`);
            }

            await this.updateAppStatus(model, appNum);
            this.showToast(`${action} completed successfully`, 'success');
        } catch (error) {
            console.error(error);
            this.showToast(error.message, 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    async handleBatchAction(event) {
        const button = event.currentTarget;
        const { action, model } = button.dataset;
        const checkedApps = document.querySelectorAll(`[data-model="${model}"] .app-checkbox:checked`);

        if (checkedApps.length === 0) {
            this.showToast('Please select at least one app', 'warning');
            return;
        }

        button.disabled = true;
        const promises = Array.from(checkedApps).map(checkbox => {
            const appCard = checkbox.closest('[data-app-id]');
            return this.handleAction({
                currentTarget: appCard.querySelector(`[data-action="${action}"]`)
            });
        });

        try {
            await Promise.all(promises);
            this.showToast(`Batch ${action} completed`, 'success');
        } catch (error) {
            this.showToast('Some batch operations failed', 'error');
        } finally {
            button.disabled = false;
        }
    }

    handleSelectAll(event) {
        const button = event.currentTarget;
        const model = button.dataset.model;
        const checkboxes = document.querySelectorAll(`[data-model="${model}"] .app-checkbox`);
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
        });
        button.textContent = allChecked ? 'Select All' : 'Deselect All';
    }

    async updateAppStatus(model, appNum) {
        try {
            const response = await fetch(`/api/container/${model}/${appNum}/status`);
            if (!response.ok) throw new Error('Failed to fetch status');

            const data = await response.json();
            const appCard = document.querySelector(`[data-app-id="${appNum}"][data-model="${model}"]`);

            if (appCard) {
                this.updateStatusUI(appCard, data);
            }
        } catch (error) {
            console.error('Status update failed:', error);
        }
    }

    updateStatusUI(appCard, status) {
        // Update backend status
        const backendStatus = appCard.querySelector('[data-status="backend"]');
        if (backendStatus) {
            backendStatus.textContent = status.backend.running ? 'Running' : 'Stopped';
            backendStatus.className = `font-medium ${status.backend.running ? 'text-green-600' : 'text-red-600'}`;
        }

        // Update frontend status
        const frontendStatus = appCard.querySelector('[data-status="frontend"]');
        if (frontendStatus) {
            frontendStatus.textContent = status.frontend.running ? 'Running' : 'Stopped';
            frontendStatus.className = `font-medium ${status.frontend.running ? 'text-green-600' : 'text-red-600'}`;
        }

        // Update status badge
        const badge = appCard.querySelector('.absolute.top-4.right-4 span');
        if (badge) {
            const isRunning = status.backend.running && status.frontend.running;
            const isPartial = status.backend.running || status.frontend.running;

            badge.className = 'px-2 py-1 text-sm rounded-full ' + (
                isRunning ? 'bg-green-100 text-green-800' :
                    isPartial ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
            );

            badge.textContent = isRunning ? 'Running' : isPartial ? 'Partial' : 'Stopped';
        }
    }

    async refreshAllStatuses() {
        const refreshBtn = document.getElementById('refreshAll');
        const originalHtml = refreshBtn.innerHTML;

        try {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = `
                <svg class="animate-spin h-5 w-5 mr-2 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
            `;

            const apps = document.querySelectorAll('[data-app-id]');
            const promises = Array.from(apps).map(app =>
                this.updateAppStatus(app.dataset.model, app.dataset.appId)
            );

            await Promise.all(promises);
            this.showToast('All statuses refreshed', 'success');
        } catch (error) {
            this.showToast('Failed to refresh all statuses', 'error');
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = originalHtml;
        }
    }

    setupAutoRefresh() {
        const button = document.getElementById('toggleAutorefresh');
        if (button) {
            const enabled = button.dataset.enabled === 'true';
            if (enabled) {
                this.startAutoRefresh();
            }
        }
    }

    toggleAutoRefresh() {
        const button = document.getElementById('toggleAutorefresh');
        const textSpan = button.querySelector('#autorefreshText');
        const isEnabled = button.dataset.enabled === 'true';

        if (isEnabled) {
            this.stopAutoRefresh();
            button.dataset.enabled = 'false';
            button.classList.remove('bg-green-500', 'hover:bg-green-600');
            button.classList.add('bg-gray-500', 'hover:bg-gray-600');
            textSpan.textContent = 'Auto Refresh: Off';
        } else {
            this.startAutoRefresh();
            button.dataset.enabled = 'true';
            button.classList.remove('bg-gray-500', 'hover:bg-gray-600');
            button.classList.add('bg-green-500', 'hover:bg-green-600');
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

    setupFilters() {
        const searchInput = document.getElementById('searchApps');
        const modelFilter = document.getElementById('filterModel');
        const statusFilter = document.getElementById('filterStatus');

        const applyFilters = () => {
            const searchTerm = searchInput.value.toLowerCase();
            const modelValue = modelFilter.value;
            const statusValue = statusFilter.value;
            let visibleCount = 0;

            // Filter app cards
            document.querySelectorAll('[data-app-id]').forEach(app => {
                // Get elements with null checks
                const appNameElement = app.querySelector('h3');
                const statusElement = app.querySelector('[class*="bg-"]'); // Changed selector to match status badge

                // Get values with fallbacks
                const appName = appNameElement?.textContent?.toLowerCase() || '';
                const model = app.dataset.model || '';
                const status = statusElement?.textContent?.toLowerCase().trim() || '';

                // Debug logging
                console.debug('Filtering:', { appName, model, status, searchTerm, modelValue, statusValue });

                const matchesSearch = appName.includes(searchTerm);
                const matchesModel = !modelValue || model === modelValue;
                const matchesStatus = !statusValue || status.includes(statusValue);

                const shouldShow = matchesSearch && matchesModel && matchesStatus;
                app.style.display = shouldShow ? '' : 'none';
                if (shouldShow) visibleCount++;
            });

            // Update model section visibility
            document.querySelectorAll('[data-model-section]').forEach(section => {
                const hasVisibleApps = Array.from(section.querySelectorAll('[data-app-id]'))
                    .some(app => app.style.display !== 'none');
                section.style.display = hasVisibleApps ? '' : 'none';
            });

            // Show/hide no results message
            const noResultsMessage = document.getElementById('noResultsMessage');
            if (noResultsMessage) {
                noResultsMessage.classList.toggle('hidden', visibleCount > 0);
            }
        };

        // Add event listeners with debounce for search
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(applyFilters, 300));
        }
        if (modelFilter) {
            modelFilter.addEventListener('change', applyFilters);
        }
        if (statusFilter) {
            statusFilter.addEventListener('change', applyFilters);
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        }[type] || 'bg-blue-500';

        toast.className = `fixed bottom-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg transform transition-transform duration-300 translate-y-full z-50`;
        toast.textContent = message;

        document.body.appendChild(toast);
        requestAnimationFrame(() => {
            toast.style.transform = 'translateY(0)';
            setTimeout(() => {
                toast.style.transform = 'translateY(100%)';
                toast.addEventListener('transitionend', () => {
                    document.body.removeChild(toast);
                });
            }, 3000);
        });
    }

    getLoadingText(action) {
        const actionTexts = {
            start: 'Starting...',
            stop: 'Stopping...',
            reload: 'Reloading...',
            rebuild: 'Rebuilding...',
            status: 'Checking...'
        };
        return actionTexts[action] || 'Working...';
    }

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
}