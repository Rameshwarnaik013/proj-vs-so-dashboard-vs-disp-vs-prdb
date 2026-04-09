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

def get_file_info():
    try:
        stat = os.stat(FILENAME)
        return stat.st_mtime, stat.st_size
    except OSError:
        return 0, 0

def watch_file():
    global last_mtime
    last_mtime, last_size = get_file_info()
    print(f"[*] Watching for changes in: {FILENAME}")
    
    while True:
        time.sleep(POLL_INTERVAL)
        curr_mtime, curr_size = get_file_info()
        
        if curr_mtime > last_mtime or curr_size != last_size:
            print(f"[!] Change detected. Waiting for file to stabilize...")
            
            # Wait for file to stop changing (essential for large 80MB files)
            stable_count = 0
            while stable_count < 3:
                time.sleep(1.0)
                check_mtime, check_size = get_file_info()
                if check_mtime == curr_mtime and check_size == curr_size:
                    stable_count += 1
                else:
                    curr_mtime, curr_size = check_mtime, check_size
                    stable_count = 0
            
            print(f"[*] File stabilized. Notifying dashboard...")
            last_mtime = curr_mtime
            last_size = curr_size
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
    def log_message(self, format, *args):
        # Only log successful updates or detections, keep the rest quiet
        if "GET /latest" in args[0]:
            print(f"[*] Dashboard updated successfully.")
        elif "GET /events" in args[0]:
            pass # Keep connection logs quiet
        else:
            # super().log_message(format, *args)
            pass

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
        # Normalize path for matching
        clean_path = self.path.split('?')[0].rstrip('/')
        
        if clean_path == '/events':
            self.handle_sse()
        elif clean_path == '/latest':
            self.handle_latest()
        else:
            # Serve static files as usual
            super().do_GET()

    def handle_sse(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            sse = SSEHandler(self)
            clients.append(sse)
            print(f"[+] Dashboard connected.")
            
            # Keep connection open
            while True:
                # Send keep-alive every 30 seconds to prevent timeout
                time.sleep(30)
                sse.send_event("ping", "keep-alive")
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass # Normal disconnection
        except Exception as e:
            pass
        finally:
            if 'sse' in locals() and sse in clients:
                clients.remove(sse)
            print(f"[-] Dashboard disconnected.")

    def handle_latest(self):
        if not os.path.exists(FILENAME):
            self.send_error(404, "File not found")
            return
            
        try:
            with open(FILENAME, 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
        except:
            pass

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    
    def handle_error(self, request, client_address):
        # Suppress the scary tracebacks for normal browser disconnections
        pass

def run_server():
    with ThreadingTCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"[*] Live Sync Server Active on http://localhost:{PORT}")
        print(f"[*] Watching: {FILENAME}")
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
