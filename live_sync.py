import http.server
import socketserver
import threading
import time
import os
import json
import webbrowser

# ============================================================
# CONFIGURATION
# ============================================================
PORT = 8080
FILENAME = "Projection vs so vs disp vs prdn dashboard.xlsx"
POLL_INTERVAL = 1.0  # Seconds

# ============================================================
# LIVE SYNC STATE
# ============================================================
clients = []
last_mtime = 0

def get_current_mtime():
    try:
        return os.path.getmtime(FILENAME)
    except OSError:
        return 0

def watch_file():
    global last_mtime
    last_mtime = get_current_mtime()
    print(f"[*] Watching for changes in: {FILENAME}")
    
    while True:
        time.sleep(POLL_INTERVAL)
        current_mtime = get_current_mtime()
        if current_mtime > last_mtime:
            print(f"[!] Change detected in {FILENAME}")
            last_mtime = current_mtime
            notify_clients()

def notify_clients():
    global clients
    disconnected = []
    for i, client in enumerate(clients):
        try:
            client.send_event("update", "File modified")
        except:
            disconnected.append(i)
    
    # Clean up disconnected clients
    for i in reversed(disconnected):
        clients.pop(i)

class SSEHandler:
    def __init__(self, request_handler):
        self.request_handler = request_handler
    
    def send_event(self, event, data):
        try:
            message = f"event: {event}\ndata: {data}\n\n"
            self.request_handler.wfile.write(message.encode('utf-8'))
            self.request_handler.wfile.flush()
        except:
            raise Exception("Client disconnected")

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With')
        self.end_headers()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        if self.path == '/events':
            self.handle_sse()
        elif self.path.startswith('/latest'):
            self.handle_latest()
        else:
            super().do_GET()

    def handle_sse(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        sse = SSEHandler(self)
        clients.append(sse)
        print(f"[+] Dashboard connected. Active clients: {len(clients)}")
        
        # Keep connection open
        while True:
            try:
                # Send keep-alive every 30 seconds
                time.sleep(30)
                sse.send_event("ping", "keep-alive")
            except:
                print(f"[-] Dashboard disconnected. Active clients: {len(clients)-1}")
                break

    def handle_latest(self):
        if not os.path.exists(FILENAME):
            self.send_error(404, "File not found")
            return
            
        with open(FILENAME, 'rb') as f:
            content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

def run_server():
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"[*] Server running at http://localhost:{PORT}")
        print(f"[*] Dashboard URL: http://localhost:{PORT}/index.html")
        # Automatically open the dashboard
        webbrowser.open(f"http://localhost:{PORT}/index.html")
        httpd.serve_forever()

if __name__ == "__main__":
    # Start watcher thread
    watcher_thread = threading.Thread(target=watch_file, daemon=True)
    watcher_thread.start()
    
    # Start server
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
