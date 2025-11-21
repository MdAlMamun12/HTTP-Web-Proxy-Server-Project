A modern, feature-rich HTTP proxy server built with Python and Flask, featuring a beautiful web interface for monitoring and management.


https://img.shields.io/badge/Status-Active-success

https://img.shields.io/badge/Python-3.7%252B-blue

https://img.shields.io/badge/Flask-2.3.3-green





🚀 Features:



Core Proxy Functionality:


HTTP Request Forwarding: Intercepts and forwards HTTP requests between clients and servers

Response Caching: Intelligent caching system for improved performance

Domain Filtering: Block specific domains with easy management

Request Logging: Comprehensive logging of all proxy traffic

Error Handling: Robust error handling for network issues




Web Interface:


Real-time Dashboard: Live statistics and monitoring

Cache Management: View and manage cached responses

Request Logs: Detailed history of all proxy requests

Domain Management: Easy blocking and unblocking of domains

Responsive Design: Works perfectly on desktop and mobile devices





Advanced Features:


Auto-refresh Statistics: Real-time updates without page reload

Test Data Generation: Populate cache with sample data for testing

Cache Control: Enable/disable caching with one click

Notification System: User-friendly feedback for all actions




📋 Requirements: 


Python 3.7+

Flask 2.3.3



🛠 Installation:

Clone or download the project files


bash

mkdir http_proxy_server

cd http_proxy_server



Save all project files in the directory:

proxy_server.py

web_interface.py

requirements.txt

templates/ directory with HTML files

static/ directory with CSS files



Install dependencies:

bash

pip install -r requirements.txt




🚀 Quick Start


Starting the Proxy Server


Run the proxy server:

bash

python proxy_server.py



You should see output similar to:


Proxy server started on localhost:8080

Web interface available at http://localhost:5000

Configure your browser to use proxy: localhost:8080


Access the web interface:

Open your browser and navigate to http://localhost:5000



Configuring Your Browser:


Firefox

Go to Settings > Network Settings

Select Manual proxy configuration

Set HTTP Proxy to localhost and Port to 8080

Check Also use this proxy for HTTPS

Click OK



Chrome (Command Line)

bash

chrome --proxy-server=http://localhost:8080


System-wide (Windows)

Go to Settings > Network & Internet > Proxy

Enable Manual proxy setup

Set Address to localhost and Port to 8080




📊 Dashboard Overview:


Statistics Cards

Total Requests: Real-time count of all proxy requests

Cached Items: Number of cached responses with total size in kB

Blocked Domains: Count of currently blocked domains

Cache Status: Current caching state (Enabled/Disabled)




Control Panels:


Quick Actions: Clear cache, add test data, toggle caching

Domain Management: View blocked domains and add new ones

Recent Activity: Live feed of recent proxy requests



🗂 Project Structure:

http_proxy_server/
├── proxy_server.py              # Main proxy server implementation

├── web_interface.py             # Flask web interface

├── requirements.txt             # Python dependencies

├── proxy.db                    # SQLite database (auto-created)

├── templates/                  # HTML templates

│   ├── index.html              # Main dashboard

│   ├── logs.html               # Request logs page

│   └── cache.html              # Cache management page

└── static/

    └── style.css               # Modern CSS styling




🔧 API Endpoints


Web Interface Routes

GET / - Main dashboard

GET /logs - Request logs

GET /cache - Cache management




API Routes


GET /api/stats - Get server statistics

GET /api/cache_stats - Get cache statistics

POST /api/clear_cache - Clear all cached data

POST /api/toggle_cache - Enable/disable caching

POST /api/add_test_cache - Add test cache data

POST /api/block_domain - Block a domain

POST /api/unblock_domain - Unblock a domain




🎯 Usage Examples


Basic Proxy Usage:

Start the proxy server

Configure your browser to use the proxy

Browse any website - requests will be logged and cached



Testing the Cache:


Click "Add Test Data" to populate cache with sample responses

Visit "Cache Manager" to view cached items

Test cache hits by visiting the same URLs multiple times



Domain Blocking:


Enter a domain (e.g., example.com) in the block domain field

Click "Block" - the domain will be immediately blocked

Attempt to visit the blocked domain to see the access denied message




🔍 Technical Details:



Caching Mechanism:


Caches only GET requests with 200 status responses

Uses SQLite database for persistent storage

Automatic cache invalidation on server restart

Configurable cache enable/disable




Database Schema"


request_logs: Timestamp, client IP, method, URL, status code, response size

cache: URL, response data, timestamp, content type

blocked_domains: List of blocked domain names



Network Handling:


Timeout Management: 5-second connection timeout, 10-second receive timeout

Error Recovery: Graceful handling of connection failures

Protocol Support: Basic HTTP protocol implementation




🎨 UI Features:



Modern Design:


Dark Theme: Easy on eyes with professional appearance

Responsive Layout: Adapts to desktop, tablet, and mobile screens

Smooth Animations: CSS transitions and hover effects

Color-coded Status: Visual indicators for different request types




Interactive Elements:


Real-time Updates: Auto-refreshing statistics

Toast Notifications: Action feedback system

Mobile Menu: Collapsible sidebar for small screens

Loading States: Visual feedback for operations




🐛 Troubleshooting


Common Issues:


Proxy connection refused:

Ensure the proxy server is running on port 8080

Check firewall settings



Web interface not accessible:


Verify Flask is installed correctly

Check if port 5000 is available



Cache not working:


Ensure caching is enabled in the dashboard

Verify only GET requests are being cached



Domain blocking not working:


Check if the domain format is correct (without http://)

Verify the domain is not already blocked




Logs and Debugging:


Check console output for error messages

Review request logs in the web interface

Monitor cache hits/misses in server logs




📈 Performance:



Cache Benefits:


Reduced Latency: Faster response times for cached content

Bandwidth Savings: Fewer requests to origin servers

Load Reduction: Decreased load on target websites



Memory Usage:


SQLite database for efficient storage

In-memory caching for frequently accessed 

Automatic cleanup of old logs




🔒 Security Notes:



Important Considerations


This is a development and educational proxy server

Do not use in production without additional security measures

HTTP traffic is not encrypted - consider HTTPS for sensitive data

Domain blocking is basic - not a replacement for enterprise security




Recommended Security Enhancements:


Add authentication to the web interface

Implement HTTPS support

Add request filtering and content inspection

Set up proper logging and monitoring




🤝 Contributing:


Feel free to contribute to this project by:

Reporting bugs

Suggesting new features

Improving documentation

Submitting pull requests




📄 License:

This project is open source and available under the MIT License.




🙏 Acknowledgments:


Built with Flask

Icons from Font Awesome

Modern CSS design inspired by current web trends
