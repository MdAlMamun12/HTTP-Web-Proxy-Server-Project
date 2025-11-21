import socket
import threading
import time
import sqlite3
import hashlib
from urllib.parse import urlparse
from http.client import HTTPResponse
from io import BytesIO
import json
import os

class HTTPProxyServer:
    def __init__(self, host='localhost', port=8080, cache_enabled=True):
        self.host = host
        self.port = port
        self.cache_enabled = cache_enabled
        self.blocked_domains = set()
        self.request_logs = []
        self.cache = {}
        self.is_running = False
        self.server_socket = None
        
        # Create templates and static directories if they don't exist
        self.create_directories()
        
        # Initialize database for persistent storage
        self.init_database()
    
    def create_directories(self):
        """Create necessary directories for the web interface"""
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)
        
        # Create the template files
        self.create_template_files()
        # Create the CSS file
        self.create_css_file()
    
    def create_template_files(self):
        """Create the HTML template files"""
        # Create index.html
        index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTTP Proxy Server</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <!-- Sidebar Navigation -->
        <nav class="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <i class="fas fa-shield-alt"></i>
                    <span>HTTP Web Proxy Server</span>
                </div>
            </div>
            <ul class="sidebar-nav">
                <li class="nav-item active">
                    <a href="{{ url_for('index') }}" class="nav-link">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a href="{{ url_for('logs') }}" class="nav-link">
                        <i class="fas fa-list-alt"></i>
                        <span>Request Logs</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a href="{{ url_for('cache_view') }}" class="nav-link">
                        <i class="fas fa-database"></i>
                        <span>Cache Manager</span>
                    </a>
                </li>
            </ul>
            <div class="sidebar-footer">
                <div class="server-status">
                    <div class="status-indicator {{ 'running' if stats.is_running else 'stopped' }}"></div>
                    <span>{{ 'Server Running' if stats.is_running else 'Server Stopped' }}</span>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Header -->
            <header class="content-header">
                <div class="header-left">
                    <h1>Proxy Server Dashboard</h1>
                    <p class="subtitle">Monitor and manage your HTTP proxy server in real-time</p>
                </div>
                <div class="header-right">
                    <div class="server-info">
                        <i class="fas fa-server"></i>
                        <span>{{ stats.server_address }}</span>
                    </div>
                </div>
            </header>

            <!-- Stats Cards -->
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-icon">
                        <i class="fas fa-exchange-alt"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Total Requests</h3>
                        <div class="stat-value">{{ stats.total_requests }}</div>
                        <div class="stat-trend">
                            <i class="fas fa-chart-line"></i>
                            <span>Real-time tracking</span>
                        </div>
                    </div>
                </div>

                <div class="stat-card success">
                    <div class="stat-icon">
                        <i class="fas fa-database"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Cached Items</h3>
                        <div class="stat-value">{{ cache_stats.total_cached }}</div>
                        <div class="stat-subtext">{{ cache_stats.cache_size_kb }} kB</div>
                    </div>
                    <a href="{{ url_for('cache_view') }}" class="stat-action">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>

                <div class="stat-card warning">
                    <div class="stat-icon">
                        <i class="fas fa-ban"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Blocked Domains</h3>
                        <div class="stat-value">{{ stats.blocked_domains }}</div>
                        <div class="stat-subtext">Access restricted</div>
                    </div>
                </div>

                <div class="stat-card info">
                    <div class="stat-icon">
                        <i class="fas fa-bolt"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Cache Status</h3>
                        <div class="stat-value">{{ 'Enabled' if proxy_server.cache_enabled else 'Disabled' }}</div>
                        <div class="stat-subtext">Performance mode</div>
                    </div>
                </div>
            </div>

            <!-- Control Panels -->
            <div class="panels-grid">
                <!-- Quick Actions Panel -->
                <div class="panel quick-actions">
                    <div class="panel-header">
                        <h2><i class="fas fa-rocket"></i> Quick Actions</h2>
                    </div>
                    <div class="panel-content">
                        <div class="action-buttons">
                            <button id="clearCacheBtn" class="btn btn-warning">
                                <i class="fas fa-broom"></i>
                                Clear Cache
                            </button>
                            <button id="addTestDataBtn" class="btn btn-info">
                                <i class="fas fa-vial"></i>
                                Add Test Data
                            </button>
                            <div class="toggle-group">
                                <label class="toggle-label">
                                    <input type="checkbox" id="cacheToggle" {{ 'checked' if proxy_server.cache_enabled else '' }}>
                                    <span class="toggle-slider"></span>
                                    <span class="toggle-text">Cache Enabled</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Domain Management Panel -->
                <div class="panel domain-management">
                    <div class="panel-header">
                        <h2><i class="fas fa-shield-alt"></i> Domain Management</h2>
                    </div>
                    <div class="panel-content">
                        <div class="blocked-list">
                            <h3>Blocked Domains</h3>
                            {% if blocked_domains %}
                            <div class="domain-list">
                                {% for domain in blocked_domains %}
                                <div class="domain-item">
                                    <span class="domain-name">{{ domain }}</span>
                                    <button class="btn btn-sm btn-danger unblock-btn" data-domain="{{ domain }}">
                                        <i class="fas fa-unlock"></i>
                                    </button>
                                </div>
                                {% endfor %}
                            </div>
                            {% else %}
                            <div class="empty-state">
                                <i class="fas fa-check-circle"></i>
                                <p>No domains blocked</p>
                            </div>
                            {% endif %}
                        </div>
                        <div class="add-domain-form">
                            <div class="input-group">
                                <input type="text" id="newDomain" placeholder="Enter domain to block (e.g., example.com)" class="form-input">
                                <button id="blockDomainBtn" class="btn btn-danger">
                                    <i class="fas fa-ban"></i>
                                    Block
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="panel recent-activity">
                <div class="panel-header">
                    <h2><i class="fas fa-clock"></i> Recent Activity</h2>
                    <a href="{{ url_for('logs') }}" class="btn btn-secondary btn-sm">
                        View All
                        <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
                <div class="panel-content">
                    {% if recent_logs %}
                    <div class="activity-list">
                        {% for log in recent_logs %}
                        <div class="activity-item">
                            <div class="activity-icon {{ log.method.lower() }}">
                                <i class="fas fa-{{ 'download' if log.method == 'GET' else 'upload' if log.method == 'POST' else 'exchange-alt' }}"></i>
                            </div>
                            <div class="activity-content">
                                <div class="activity-main">
                                    <span class="activity-method {{ log.method.lower() }}">{{ log.method }}</span>
                                    <span class="activity-url">{{ log.url }}</span>
                                </div>
                                <div class="activity-meta">
                                    <span class="activity-time">{{ log.timestamp }}</span>
                                    <span class="activity-status status-{{ log.status_code // 100 }}">{{ log.status_code }}</span>
                                    <span class="activity-size">{{ log.response_size }} bytes</span>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No recent activity</p>
                        <small>Proxy requests will appear here</small>
                    </div>
                    {% endif %}
                </div>
            </div>
        </main>
    </div>

    <script>
        // Cache Management
        document.getElementById('clearCacheBtn').addEventListener('click', function() {
            if (confirm('Are you sure you want to clear all cached data?')) {
                fetch('/api/clear_cache', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification('Cache cleared successfully', 'success');
                            setTimeout(() => location.reload(), 1000);
                        }
                    });
            }
        });

        document.getElementById('addTestDataBtn').addEventListener('click', function() {
            fetch('/api/add_test_cache', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Test cache data added successfully', 'success');
                        setTimeout(() => location.reload(), 1000);
                    }
                });
        });

        // Cache Toggle
        document.getElementById('cacheToggle').addEventListener('change', function() {
            fetch('/api/toggle_cache', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'enabled=' + this.checked
            }).then(() => {
                showNotification('Cache ' + (this.checked ? 'enabled' : 'disabled'), 'info');
            });
        });

        // Domain Management
        document.getElementById('blockDomainBtn').addEventListener('click', function() {
            const domain = document.getElementById('newDomain').value.trim();
            if (domain) {
                fetch('/api/block_domain', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'domain=' + encodeURIComponent(domain)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Domain ' + domain + ' blocked successfully', 'success');
                        document.getElementById('newDomain').value = '';
                        setTimeout(() => location.reload(), 1000);
                    }
                });
            } else {
                showNotification('Please enter a domain name', 'error');
            }
        });

        document.querySelectorAll('.unblock-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const domain = this.getAttribute('data-domain');
                if (domain && confirm('Unblock ' + domain + '?')) {
                    fetch('/api/unblock_domain', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: 'domain=' + encodeURIComponent(domain)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification('Domain ' + domain + ' unblocked', 'success');
                            setTimeout(() => location.reload(), 1000);
                        }
                    });
                }
            });
        });

        // Auto-refresh stats
        setInterval(() => {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    // Update total requests with animation
                    const requestElement = document.querySelector('.stat-card.primary .stat-value');
                    if (requestElement.textContent != data.total_requests) {
                        requestElement.style.transform = 'scale(1.1)';
                        setTimeout(() => {
                            requestElement.textContent = data.total_requests;
                            requestElement.style.transform = 'scale(1)';
                        }, 200);
                    }
                });
        }, 3000);

        // Notification system
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            document.body.appendChild(notification);
            setTimeout(() => notification.classList.add('show'), 100);
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 4000);
        }

        // Mobile sidebar toggle
        document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.querySelector('.sidebar');
            const mainContent = document.querySelector('.main-content');
            
            // Add mobile menu button
            const menuBtn = document.createElement('button');
            menuBtn.className = 'mobile-menu-btn';
            menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
            document.querySelector('.content-header').prepend(menuBtn);
            
            menuBtn.addEventListener('click', function() {
                sidebar.classList.toggle('mobile-open');
                mainContent.classList.toggle('sidebar-open');
            });
        });
    </script>
</body>
</html>'''
        
        # Create logs.html
        logs_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Request Logs - Proxy Server</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <nav class="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <i class="fas fa-shield-alt"></i>
                    <span>HTTP Web Proxy Server</span>
                </div>
            </div>
            <ul class="sidebar-nav">
                <li class="nav-item">
                    <a href="{{ url_for('index') }}" class="nav-link">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </a>
                </li>
                <li class="nav-item active">
                    <a href="{{ url_for('logs') }}" class="nav-link">
                        <i class="fas fa-list-alt"></i>
                        <span>Request Logs</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a href="{{ url_for('cache_view') }}" class="nav-link">
                        <i class="fas fa-database"></i>
                        <span>Cache Manager</span>
                    </a>
                </li>
            </ul>
        </nav>

        <main class="main-content">
            <header class="content-header">
                <div class="header-left">
                    <h1>Request Logs</h1>
                    <p class="subtitle">Detailed history of all proxy requests</p>
                </div>
                <div class="header-actions">
                    <a href="{{ url_for('index') }}" class="btn btn-secondary">
                        <i class="fas fa-arrow-left"></i>
                        Back to Dashboard
                    </a>
                </div>
            </header>

            <div class="panel">
                <div class="panel-header">
                    <h2><i class="fas fa-history"></i> Recent Requests ({{ logs|length }} total)</h2>
                    <div class="panel-actions">
                        <button class="btn btn-secondary btn-sm" onclick="location.reload()">
                            <i class="fas fa-sync-alt"></i>
                            Refresh
                        </button>
                    </div>
                </div>
                <div class="panel-content">
                    {% if logs %}
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Client IP</th>
                                    <th>Method</th>
                                    <th>URL</th>
                                    <th>Status</th>
                                    <th>Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for log in logs %}
                                <tr>
                                    <td class="timestamp">{{ log.timestamp }}</td>
                                    <td class="ip-address">{{ log.client_ip }}</td>
                                    <td>
                                        <span class="method-badge {{ log.method.lower() }}">
                                            <i class="fas fa-{{ 'download' if log.method == 'GET' else 'upload' if log.method == 'POST' else 'exchange-alt' }}"></i>
                                            {{ log.method }}
                                        </span>
                                    </td>
                                    <td class="url-cell">{{ log.url }}</td>
                                    <td>
                                        <span class="status-badge status-{{ log.status_code // 100 }}">
                                            {{ log.status_code }}
                                        </span>
                                    </td>
                                    <td class="size">{{ log.response_size }} bytes</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <h3>No Request Logs</h3>
                        <p>Proxy requests will appear here once traffic starts flowing through your server.</p>
                        <a href="{{ url_for('index') }}" class="btn btn-primary">
                            <i class="fas fa-tachometer-alt"></i>
                            Go to Dashboard
                        </a>
                    </div>
                    {% endif %}
                </div>
            </div>
        </main>
    </div>
</body>
</html>'''
        
        # Create cache.html
        cache_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cache Manager - Proxy Server</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <nav class="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <i class="fas fa-shield-alt"></i>
                    <span>HTTP Web Proxy Server</span>
                </div>
            </div>
            <ul class="sidebar-nav">
                <li class="nav-item">
                    <a href="{{ url_for('index') }}" class="nav-link">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </a>
                </li>
                <li class="nav-item">
                    <a href="{{ url_for('logs') }}" class="nav-link">
                        <i class="fas fa-list-alt"></i>
                        <span>Request Logs</span>
                    </a>
                </li>
                <li class="nav-item active">
                    <a href="{{ url_for('cache_view') }}" class="nav-link">
                        <i class="fas fa-database"></i>
                        <span>Cache Manager</span>
                    </a>
                </li>
            </ul>
        </nav>

        <main class="main-content">
            <header class="content-header">
                <div class="header-left">
                    <h1>Cache Manager</h1>
                    <p class="subtitle">Manage and monitor cached responses</p>
                </div>
                <div class="header-actions">
                    <a href="{{ url_for('index') }}" class="btn btn-secondary">
                        <i class="fas fa-arrow-left"></i>
                        Back to Dashboard
                    </a>
                </div>
            </header>

            <!-- Cache Statistics -->
            <div class="stats-grid compact">
                <div class="stat-card primary">
                    <div class="stat-icon">
                        <i class="fas fa-archive"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Total Items</h3>
                        <div class="stat-value">{{ cache_stats.total_cached }}</div>
                    </div>
                </div>

                <div class="stat-card success">
                    <div class="stat-icon">
                        <i class="fas fa-weight-hanging"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Total Size</h3>
                        <div class="stat-value">{{ cache_stats.cache_size_kb }}</div>
                        <div class="stat-subtext">kB</div>
                    </div>
                </div>

                <div class="stat-card info">
                    <div class="stat-icon">
                        <i class="fas fa-layer-group"></i>
                    </div>
                    <div class="stat-content">
                        <h3>Content Types</h3>
                        <div class="stat-value">{{ cache_stats.cache_by_type|length }}</div>
                        <div class="stat-subtext">Different types</div>
                    </div>
                </div>
            </div>

            <div class="panels-grid">
                <!-- Cache Actions -->
                <div class="panel cache-actions">
                    <div class="panel-header">
                        <h2><i class="fas fa-cogs"></i> Cache Controls</h2>
                    </div>
                    <div class="panel-content">
                        <div class="action-grid">
                            <button id="clearCacheBtn" class="action-btn danger">
                                <i class="fas fa-broom"></i>
                                <span>Clear All Cache</span>
                                <small>Remove all cached data</small>
                            </button>
                            <button id="addTestDataBtn" class="action-btn info">
                                <i class="fas fa-vial"></i>
                                <span>Add Test Data</span>
                                <small>Populate with sample data</small>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Content Type Breakdown -->
                {% if cache_stats.cache_by_type %}
                <div class="panel content-types">
                    <div class="panel-header">
                        <h2><i class="fas fa-chart-pie"></i> Content Types</h2>
                    </div>
                    <div class="panel-content">
                        <div class="type-list">
                            {% for item in cache_stats.cache_by_type %}
                            <div class="type-item">
                                <div class="type-info">
                                    <span class="type-name">{{ item.content_type }}</span>
                                    <span class="type-count">{{ item.count }} items</span>
                                </div>
                                <div class="type-size">{{ item.size }} bytes</div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- Cached Items -->
            <div class="panel cached-items">
                <div class="panel-header">
                    <h2><i class="fas fa-database"></i> Cached Items ({{ cached_items|length }} total)</h2>
                    <div class="panel-actions">
                        <button class="btn btn-secondary btn-sm" onclick="location.reload()">
                            <i class="fas fa-sync-alt"></i>
                            Refresh
                        </button>
                    </div>
                </div>
                <div class="panel-content">
                    {% if cached_items %}
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>URL</th>
                                    <th>Content Type</th>
                                    <th>Cached At</th>
                                    <th>Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for item in cached_items %}
                                <tr>
                                    <td class="url-cell">{{ item.url }}</td>
                                    <td>
                                        <span class="content-type-badge">{{ item.content_type }}</span>
                                    </td>
                                    <td class="timestamp">{{ item.timestamp }}</td>
                                    <td class="size">{{ item.size }} bytes</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <div class="empty-state">
                        <i class="fas fa-database"></i>
                        <h3>Cache is Empty</h3>
                        <p>No items are currently cached. Cache will populate automatically as you browse through the proxy.</p>
                        <div class="empty-state-actions">
                            <button id="addTestDataBtn2" class="btn btn-primary">
                                <i class="fas fa-vial"></i>
                                Add Test Data
                            </button>
                            <a href="{{ url_for('index') }}" class="btn btn-secondary">
                                <i class="fas fa-tachometer-alt"></i>
                                Go to Dashboard
                            </a>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </main>
    </div>

    <script>
        // Cache actions
        document.getElementById('clearCacheBtn')?.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear all cached data? This action cannot be undone.')) {
                fetch('/api/clear_cache', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification('Cache cleared successfully', 'success');
                            setTimeout(() => location.reload(), 1000);
                        }
                    });
            }
        });

        const addTestData = () => {
            fetch('/api/add_test_cache', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Test cache data added successfully', 'success');
                        setTimeout(() => location.reload(), 1000);
                    }
                });
        };

        document.getElementById('addTestDataBtn')?.addEventListener('click', addTestData);
        document.getElementById('addTestDataBtn2')?.addEventListener('click', addTestData);

        // Notification system
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            document.body.appendChild(notification);
            setTimeout(() => notification.classList.add('show'), 100);
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 4000);
        }
    </script>
</body>
</html>'''
        
        # Write template files with proper encoding
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        with open('templates/logs.html', 'w', encoding='utf-8') as f:
            f.write(logs_html)
            
        with open('templates/cache.html', 'w', encoding='utf-8') as f:
            f.write(cache_html)
    
    def create_css_file(self):
        """Create the CSS file"""
        css_content = '''/* Modern CSS Reset and Variables */
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #64748b;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --info: #06b6d4;
    
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: #334155;
    --bg-sidebar: #1e293b;
    
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    
    --border-color: #475569;
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    
    --sidebar-width: 280px;
    --header-height: 80px;
    --border-radius: 12px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
}

/* App Layout */
.app-container {
    display: flex;
    min-height: 100vh;
}

/* Sidebar */
.sidebar {
    width: var(--sidebar-width);
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    z-index: 1000;
    transition: var(--transition);
}

.sidebar-header {
    padding: 2rem 1.5rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
}

.logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.logo i {
    color: var(--primary);
    font-size: 1.75rem;
}

.sidebar-nav {
    flex: 1;
    padding: 1.5rem 0;
    list-style: none;
}

.nav-item {
    margin: 0.25rem 1rem;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--border-radius);
    transition: var(--transition);
    font-weight: 500;
}

.nav-link:hover {
    background: var(--bg-card);
    color: var(--text-primary);
    transform: translateX(4px);
}

.nav-item.active .nav-link {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    box-shadow: var(--shadow);
}

.nav-link i {
    width: 20px;
    text-align: center;
}

.sidebar-footer {
    padding: 1.5rem;
    border-top: 1px solid var(--border-color);
}

.server-status {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transition: var(--transition);
}

.status-indicator.running {
    background: var(--success);
    box-shadow: 0 0 10px var(--success);
}

.status-indicator.stopped {
    background: var(--danger);
    box-shadow: 0 0 10px var(--danger);
}

/* Main Content */
.main-content {
    flex: 1;
    margin-left: var(--sidebar-width);
    padding: 2rem;
    transition: var(--transition);
}

.content-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
}

.header-left h1 {
    font-size: 2.25rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--text-primary), var(--primary));
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: var(--text-secondary);
    font-size: 1.1rem;
}

.server-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--bg-card);
    border-radius: var(--border-radius);
    border: 1px solid var(--border-color);
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stats-grid.compact {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.stat-card {
    background: var(--bg-card);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    border: 1px solid var(--border-color);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, currentColor, transparent);
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.stat-card.primary::before { color: var(--primary); }
.stat-card.success::before { color: var(--success); }
.stat-card.warning::before { color: var(--warning); }
.stat-card.danger::before { color: var(--danger); }
.stat-card.info::before { color: var(--info); }

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}

.stat-card.primary .stat-icon { background: rgba(99, 102, 241, 0.2); color: var(--primary); }
.stat-card.success .stat-icon { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.stat-card.warning .stat-icon { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
.stat-card.danger .stat-icon { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
.stat-card.info .stat-icon { background: rgba(6, 182, 212, 0.2); color: var(--info); }

.stat-content {
    flex: 1;
}

.stat-content h3 {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stat-value {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
    transition: var(--transition);
}

.stat-subtext {
    font-size: 0.875rem;
    color: var(--text-muted);
}

.stat-trend {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--success);
    margin-top: 0.5rem;
}

.stat-action {
    color: var(--text-secondary);
    text-decoration: none;
    transition: var(--transition);
    padding: 0.5rem;
    border-radius: 8px;
}

.stat-action:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
}

/* Panels */
.panels-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.panel {
    background: var(--bg-card);
    border-radius: var(--border-radius);
    border: 1px solid var(--border-color);
    overflow: hidden;
}

.panel-header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-header h2 {
    font-size: 1.25rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.panel-content {
    padding: 1.5rem;
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: var(--border-radius);
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: var(--transition);
    font-size: 0.875rem;
}

.btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.75rem;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}

.btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background: var(--bg-card);
    transform: translateY(-2px);
}

.btn-success {
    background: var(--success);
    color: white;
}

.btn-warning {
    background: var(--warning);
    color: white;
}

.btn-danger {
    background: var(--danger);
    color: white;
}

.btn-info {
    background: var(--info);
    color: white;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow);
}

/* Action Buttons */
.action-buttons {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.toggle-group {
    display: flex;
    align-items: center;
}

.toggle-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    font-weight: 500;
}

.toggle-slider {
    width: 50px;
    height: 26px;
    background: var(--bg-secondary);
    border-radius: 25px;
    position: relative;
    transition: var(--transition);
}

.toggle-slider::before {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    background: var(--text-secondary);
    border-radius: 50%;
    top: 3px;
    left: 3px;
    transition: var(--transition);
}

#cacheToggle:checked + .toggle-slider {
    background: var(--success);
}

#cacheToggle:checked + .toggle-slider::before {
    transform: translateX(24px);
    background: white;
}

#cacheToggle {
    display: none;
}

/* Domain Management */
.domain-list {
    max-height: 200px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.domain-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border-radius: 8px;
    margin-bottom: 0.5rem;
}

.domain-name {
    font-weight: 500;
}

.input-group {
    display: flex;
    gap: 0.5rem;
}

.form-input {
    flex: 1;
    padding: 0.75rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    color: var(--text-primary);
    font-size: 0.875rem;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* Activity List */
.activity-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.activity-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: var(--border-radius);
    transition: var(--transition);
}

.activity-item:hover {
    background: var(--bg-sidebar);
    transform: translateX(4px);
}

.activity-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
}

.activity-icon.get { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.activity-icon.post { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.activity-icon.put { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
.activity-icon.delete { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

.activity-content {
    flex: 1;
}

.activity-main {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.25rem;
}

.activity-method {
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
}

.activity-method.get { background: var(--success); color: white; }
.activity-method.post { background: #3b82f6; color: white; }
.activity-method.put { background: var(--warning); color: white; }
.activity-method.delete { background: var(--danger); color: white; }

.activity-url {
    color: var(--text-primary);
    font-weight: 500;
    flex: 1;
}

.activity-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: var(--text-muted);
}

.activity-status {
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.75rem;
}

.status-2 { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.status-3 { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.status-4 { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
.status-5 { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

/* Tables */
.table-container {
    overflow-x: auto;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th,
.data-table td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.data-table th {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.data-table tr:hover {
    background: var(--bg-secondary);
}

.method-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
}

.method-badge.get { background: var(--success); color: white; }
.method-badge.post { background: #3b82f6; color: white; }
.method-badge.put { background: var(--warning); color: white; }
.method-badge.delete { background: var(--danger); color: white; }

.status-badge {
    padding: 0.375rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
}

.content-type-badge {
    padding: 0.375rem 0.75rem;
    background: var(--bg-secondary);
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
}

.url-cell {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Empty States */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--text-secondary);
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state h3 {
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.empty-state-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1.5rem;
}

/* Notifications */
.notification {
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    box-shadow: var(--shadow-lg);
    transform: translateX(400px);
    opacity: 0;
    transition: var(--transition);
    z-index: 10000;
}

.notification.show {
    transform: translateX(0);
    opacity: 1;
}

.notification.success {
    border-left: 4px solid var(--success);
}

.notification.error {
    border-left: 4px solid var(--danger);
}

.notification.info {
    border-left: 4px solid var(--info);
}

.notification button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
}

.notification button:hover {
    background: rgba(255, 255, 255, 0.1);
}

/* Action Grid */
.action-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    color: var(--text-primary);
    cursor: pointer;
    transition: var(--transition);
    text-align: center;
}

.action-btn:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow);
}

.action-btn.danger:hover {
    background: var(--danger);
    color: white;
}

.action-btn.info:hover {
    background: var(--info);
    color: white;
}

.action-btn i {
    font-size: 1.5rem;
}

.action-btn span {
    font-weight: 600;
}

.action-btn small {
    font-size: 0.75rem;
    opacity: 0.8;
}

/* Type List */
.type-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.type-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border-radius: 8px;
}

.type-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.type-name {
    font-weight: 500;
}

.type-count {
    font-size: 0.875rem;
    color: var(--text-muted);
}

.type-size {
    font-weight: 600;
    color: var(--text-primary);
}

/* Mobile Responsive */
@media (max-width: 1024px) {
    .sidebar {
        transform: translateX(-100%);
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .sidebar.mobile-open {
        transform: translateX(0);
    }
    
    .mobile-menu-btn {
        display: block !important;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        padding: 0.75rem;
        border-radius: var(--border-radius);
        cursor: pointer;
    }
}

@media (max-width: 768px) {
    .main-content {
        padding: 1rem;
    }
    
    .content-header {
        flex-direction: column;
        gap: 1rem;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .panels-grid {
        grid-template-columns: 1fr;
    }
    
    .action-buttons {
        flex-direction: column;
    }
    
    .input-group {
        flex-direction: column;
    }
    
    .empty-state-actions {
        flex-direction: column;
    }
    
    .activity-meta {
        flex-wrap: wrap;
        gap: 0.5rem;
    }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* Mobile Menu Button */
.mobile-menu-btn {
    display: none;
    background: none;
    border: none;
    color: var(--text-primary);
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
}

.mobile-menu-btn:hover {
    background: var(--bg-secondary);
}'''
        
        with open('static/style.css', 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def init_database(self):
        """Initialize SQLite database for logs and cache"""
        self.conn = sqlite3.connect('proxy.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Create logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                client_ip TEXT,
                method TEXT,
                url TEXT,
                status_code INTEGER,
                response_size INTEGER
            )
        ''')
        
        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                url TEXT PRIMARY KEY,
                response_data BLOB,
                timestamp TEXT,
                content_type TEXT
            )
        ''')
        
        # Create blocked domains table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_domains (
                domain TEXT PRIMARY KEY
            )
        ''')
        
        # Load blocked domains from database
        cursor.execute("SELECT domain FROM blocked_domains")
        self.blocked_domains = set(row[0] for row in cursor.fetchall())
        
        self.conn.commit()
    
    def start_server(self):
        """Start the proxy server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            print(f"Proxy server started on {self.host}:{self.port}")
            print(f"Web interface available at http://localhost:5000")
            print(f"Configure your browser to use proxy: {self.host}:{self.port}")
            
            # Start web interface in a separate thread
            web_interface_thread = threading.Thread(target=self.start_web_interface, daemon=True)
            web_interface_thread.start()
            
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except OSError:
                    # Socket closed, break the loop
                    break
                    
        except Exception as e:
            print(f"Error starting server: {e}")
    
    def stop_server(self):
        """Stop the proxy server"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.conn:
            self.conn.close()
        print("Proxy server stopped")
    
    def handle_client(self, client_socket, client_address):
        """Handle client connection"""
        try:
            # Receive request from client
            request_data = client_socket.recv(4096)
            if not request_data:
                return
            
            # Parse the request
            request_lines = request_data.decode('utf-8', errors='ignore').split('\r\n')
            if not request_lines or not request_lines[0]:
                return
            
            # Parse request line
            request_parts = request_lines[0].split(' ')
            if len(request_parts) < 2:
                return
            
            method = request_parts[0]
            url = request_parts[1]
            
            # Extract host and port from request headers
            host = None
            port = 80
            
            for line in request_lines[1:]:
                if line.lower().startswith('host:'):
                    host_part = line.split(':', 1)[1].strip()
                    if ':' in host_part:
                        host, port_str = host_part.split(':', 1)
                        port = int(port_str)
                    else:
                        host = host_part
                    break
            
            if not host:
                # Try to extract from URL
                if url.startswith('http://') or url.startswith('https://'):
                    parsed_url = urlparse(url)
                    if parsed_url.hostname:
                        host = parsed_url.hostname
                        port = parsed_url.port or (80 if parsed_url.scheme == 'http' else 443)
                else:
                    # Assume it's a hostname
                    host = url.split('/')[0] if '/' in url else url
                    port = 80
            
            if not host:
                print("Could not determine host from request")
                return
            
            # Check if domain is blocked
            if host in self.blocked_domains:
                self.send_blocked_response(client_socket, host)
                self.log_request(client_address[0], method, url, 403, 0)
                return
            
            # Check cache for GET requests
            if method == 'GET' and self.cache_enabled:
                cached_response = self.get_cached_response(url)
                if cached_response:
                    print(f"Cache HIT: {url}")
                    client_socket.sendall(cached_response)
                    self.log_request(client_address[0], method, url, 200, len(cached_response))
                    return
                else:
                    print(f"Cache MISS: {url}")
            
            # Forward request to destination server with better error handling
            try:
                # Create socket with shorter timeout for faster failure
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.settimeout(5)  # Reduced timeout from 10 to 5 seconds
                
                print(f"Attempting to connect to {host}:{port}")
                server_socket.connect((host, port))
                print(f"Connected to {host}:{port}")
                
                # Send the original request
                server_socket.sendall(request_data)
                
                # Receive response from server
                response_data = b''
                server_socket.settimeout(10)  # Longer timeout for receiving data
                
                while True:
                    try:
                        chunk = server_socket.recv(4096)
                        if not chunk:
                            break
                        response_data += chunk
                    except socket.timeout:
                        # No more data to receive
                        break
                
                server_socket.close()
                
                if response_data:
                    # Cache the response if it's cacheable (GET requests with status 200)
                    if method == 'GET' and self.cache_enabled:
                        status_code = self.extract_status_code(response_data)
                        if status_code == 200:
                            print(f"Caching response for: {url}")
                            self.cache_response(url, response_data)
                    
                    # Send response back to client
                    client_socket.sendall(response_data)
                    
                    # Log the request
                    status_code = self.extract_status_code(response_data)
                    self.log_request(client_address[0], method, url, status_code, len(response_data))
                else:
                    self.send_error_response(client_socket, 502, "Empty Response from Server")
                    self.log_request(client_address[0], method, url, 502, 0)
                
            except socket.timeout:
                print(f"Connection timeout to {host}:{port}")
                self.send_error_response(client_socket, 504, "Gateway Timeout")
                self.log_request(client_address[0], method, url, 504, 0)
            except ConnectionRefusedError:
                print(f"Connection refused by {host}:{port}")
                self.send_error_response(client_socket, 502, "Connection Refused")
                self.log_request(client_address[0], method, url, 502, 0)
            except Exception as e:
                print(f"Error forwarding request to {host}:{port}: {e}")
                self.send_error_response(client_socket, 502, "Bad Gateway")
                self.log_request(client_address[0], method, url, 502, 0)
        
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def add_test_cache_data(self):
        """Add test cache data for demonstration"""
        test_responses = {
            "http://example.com/test1": {
                "content": b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Test Page 1</h1></body></html>",
                "content_type": "text/html"
            },
            "http://example.com/test2": {
                "content": b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"message\": \"Test JSON data\", \"status\": \"success\"}",
                "content_type": "application/json"
            },
            "http://test.com/data": {
                "content": b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nThis is test plain text content for caching demonstration.",
                "content_type": "text/plain"
            },
            "http://demo.org/api/info": {
                "content": b"HTTP/1.1 200 OK\r\nContent-Type: application/xml\r\n\r\n<response><status>success</status><data>Test XML data</data></response>",
                "content_type": "application/xml"
            }
        }
        
        for url, data in test_responses.items():
            self.cache_response(url, data["content"])
        
        print("Added test cache data")
    
    def get_cached_response(self, url):
        """Get cached response for URL"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT response_data FROM cache WHERE url = ?", (url,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def cache_response(self, url, response_data):
        """Cache response for URL"""
        try:
            cursor = self.conn.cursor()
            content_type = self.extract_content_type(response_data)
            cursor.execute(
                "INSERT OR REPLACE INTO cache (url, response_data, timestamp, content_type) VALUES (?, ?, ?, ?)",
                (url, response_data, time.time(), content_type)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Error caching response: {e}")
    
    def extract_content_type(self, response_data):
        """Extract content type from response"""
        try:
            response_str = response_data.decode('utf-8', errors='ignore')
            headers_end = response_str.find('\r\n\r\n')
            if headers_end != -1:
                headers = response_str[:headers_end]
                for line in headers.split('\r\n'):
                    if line.lower().startswith('content-type:'):
                        return line.split(':', 1)[1].strip()
        except:
            pass
        return 'unknown'
    
    def extract_status_code(self, response_data):
        """Extract status code from response"""
        try:
            response_str = response_data.decode('utf-8', errors='ignore')
            first_line = response_str.split('\r\n')[0]
            return int(first_line.split(' ')[1])
        except:
            return 0
    
    def log_request(self, client_ip, method, url, status_code, response_size):
        """Log request to database"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO request_logs (timestamp, client_ip, method, url, status_code, response_size) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, client_ip, method, url, status_code, response_size)
        )
        self.conn.commit()
        
        # Also keep in memory for quick access
        log_entry = {
            'timestamp': timestamp,
            'client_ip': client_ip,
            'method': method,
            'url': url,
            'status_code': status_code,
            'response_size': response_size
        }
        self.request_logs.append(log_entry)
        
        # Keep only last 1000 logs in memory
        if len(self.request_logs) > 1000:
            self.request_logs = self.request_logs[-1000:]
    
    def send_blocked_response(self, client_socket, domain):
        """Send blocked domain response"""
        response = f"""HTTP/1.1 403 Forbidden
Content-Type: text/html
Connection: close

<html>
<head><title>Access Denied</title></head>
<body>
<h1>403 Forbidden</h1>
<p>Access to {domain} has been blocked by the proxy server.</p>
</body>
</html>"""
        client_socket.sendall(response.encode('utf-8'))
    
    def send_error_response(self, client_socket, status_code, message):
        """Send error response"""
        response = f"""HTTP/1.1 {status_code} {message}
Content-Type: text/html
Connection: close

<html>
<head><title>Error {status_code}</title></head>
<body>
<h1>{status_code} {message}</h1>
<p>The proxy server encountered an error while processing your request.</p>
</body>
</html>"""
        client_socket.sendall(response.encode('utf-8'))
    
    def add_blocked_domain(self, domain):
        """Add domain to blocked list"""
        self.blocked_domains.add(domain)
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO blocked_domains (domain) VALUES (?)", (domain,))
        self.conn.commit()
    
    def remove_blocked_domain(self, domain):
        """Remove domain from blocked list"""
        if domain in self.blocked_domains:
            self.blocked_domains.remove(domain)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM blocked_domains WHERE domain = ?", (domain,))
        self.conn.commit()
    
    def clear_cache(self):
        """Clear the cache"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM cache")
        self.conn.commit()
        self.cache.clear()
        print("Cache cleared")
    
    def get_stats(self):
        """Get proxy server statistics"""
        cursor = self.conn.cursor()
        
        # Total requests
        cursor.execute("SELECT COUNT(*) FROM request_logs")
        total_requests = cursor.fetchone()[0]
        
        # Cache hits
        cursor.execute("SELECT COUNT(*) FROM cache")
        cached_items = cursor.fetchone()[0]
        
        # Blocked domains count
        blocked_count = len(self.blocked_domains)
        
        return {
            'total_requests': total_requests,
            'cached_items': cached_items,
            'blocked_domains': blocked_count,
            'is_running': self.is_running,
            'server_address': f"{self.host}:{self.port}"
        }
    
    def get_cache_stats(self):
        """Get detailed cache statistics"""
        cursor = self.conn.cursor()
        
        # Total cached items
        cursor.execute("SELECT COUNT(*) FROM cache")
        total_cached = cursor.fetchone()[0]
        
        # Cache size in kB
        cursor.execute("SELECT SUM(LENGTH(response_data)) FROM cache")
        cache_size_bytes = cursor.fetchone()[0] or 0
        cache_size_kb = round(cache_size_bytes / 1024, 2)
        
        # Cache by content type
        cursor.execute("""
            SELECT content_type, COUNT(*) as count, SUM(LENGTH(response_data)) as size 
            FROM cache 
            GROUP BY content_type
        """)
        cache_by_type = []
        for row in cursor.fetchall():
            cache_by_type.append({
                'content_type': row[0],
                'count': row[1],
                'size': row[2]
            })
        
        return {
            'total_cached': total_cached,
            'cache_size_kb': cache_size_kb,
            'cache_by_type': cache_by_type
        }
    
    def get_cached_urls(self):
        """Get list of cached URLs"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT url, content_type, timestamp, LENGTH(response_data) as size 
            FROM cache 
            ORDER BY timestamp DESC
        """)
        cached_items = []
        for row in cursor.fetchall():
            cached_items.append({
                'url': row[0],
                'content_type': row[1],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(row[2]))),
                'size': row[3]
            })
        return cached_items
    
    def get_recent_logs(self, limit=50):
        """Get recent request logs"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT timestamp, client_ip, method, url, status_code, response_size FROM request_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'timestamp': row[0],
                'client_ip': row[1],
                'method': row[2],
                'url': row[3],
                'status_code': row[4],
                'response_size': row[5]
            })
        return logs
    
    def start_web_interface(self):
        """Start the web interface for monitoring"""
        from web_interface import app
        app.proxy_server = self
        
        # Set template folder explicitly
        app.template_folder = 'templates'
        app.static_folder = 'static'
        
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# For standalone execution
if __name__ == "__main__":
    proxy = HTTPProxyServer(port=8080)
    try:
        proxy.start_server()
    except KeyboardInterrupt:
        proxy.stop_server()