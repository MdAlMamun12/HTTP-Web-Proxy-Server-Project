from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.proxy_server = None

@app.route('/')
def index():
    if not app.proxy_server:
        return "Proxy server not initialized"
    
    stats = app.proxy_server.get_stats()
    blocked_domains = list(app.proxy_server.blocked_domains)
    recent_logs = app.proxy_server.get_recent_logs(10)
    cache_stats = app.proxy_server.get_cache_stats()
    
    return render_template('index.html', 
                         stats=stats, 
                         blocked_domains=blocked_domains,
                         recent_logs=recent_logs,
                         cache_stats=cache_stats,
                         proxy_server=app.proxy_server)

@app.route('/logs')
def logs():
    if not app.proxy_server:
        return "Proxy server not initialized"
    
    logs = app.proxy_server.get_recent_logs(100)
    return render_template('logs.html', logs=logs)

@app.route('/cache')
def cache_view():
    if not app.proxy_server:
        return "Proxy server not initialized"
    
    cached_items = app.proxy_server.get_cached_urls()
    cache_stats = app.proxy_server.get_cache_stats()
    
    return render_template('cache.html', 
                         cached_items=cached_items,
                         cache_stats=cache_stats)

@app.route('/api/stats')
def api_stats():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    return jsonify(app.proxy_server.get_stats())

@app.route('/api/cache_stats')
def api_cache_stats():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    return jsonify(app.proxy_server.get_cache_stats())

@app.route('/api/block_domain', methods=['POST'])
def api_block_domain():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    domain = request.form.get('domain')
    if domain:
        app.proxy_server.add_blocked_domain(domain)
        return jsonify({'success': True})
    
    return jsonify({'error': 'No domain provided'})

@app.route('/api/unblock_domain', methods=['POST'])
def api_unblock_domain():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    domain = request.form.get('domain')
    if domain:
        app.proxy_server.remove_blocked_domain(domain)
        return jsonify({'success': True})
    
    return jsonify({'error': 'No domain provided'})

@app.route('/api/clear_cache', methods=['POST'])
def api_clear_cache():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    app.proxy_server.clear_cache()
    return jsonify({'success': True})

@app.route('/api/toggle_cache', methods=['POST'])
def api_toggle_cache():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    enabled = request.form.get('enabled') == 'true'
    app.proxy_server.cache_enabled = enabled
    return jsonify({'success': True, 'cache_enabled': enabled})

@app.route('/api/add_test_cache', methods=['POST'])
def api_add_test_cache():
    if not app.proxy_server:
        return jsonify({'error': 'Proxy server not initialized'})
    
    app.proxy_server.add_test_cache_data()
    return jsonify({'success': True})

if __name__ == "__main__":
    # This will be called when running web_interface directly
    # Normally, the proxy server will start the web interface
    from proxy_server import HTTPProxyServer
    app.proxy_server = HTTPProxyServer(port=8080)
    
    # Start proxy in a separate thread
    import threading
    proxy_thread = threading.Thread(target=app.proxy_server.start_server, daemon=True)
    proxy_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)