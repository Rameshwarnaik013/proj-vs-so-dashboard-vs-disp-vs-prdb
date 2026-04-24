import http.server
import socketserver
import threading
import time
import os
import json
import webbrowser
import sys
import traceback
from data_processor import process_excel_data
import queue

# ============================================================
# CONFIGURATION
# ============================================================
PORT = 8080
FILENAME = "Projection vs so vs disp vs prdn dashboard.xlsx"
POLL_INTERVAL = 1.0  # Seconds
HEARTBEAT_INTERVAL = 5 # More frequent pings for live progress

# ============================================================
clients = []
last_mtime = 0
cached_data = None
is_processing = False
current_status = "Connected"

def get_file_info():
    try:
        if not os.path.exists(FILENAME):
            return 0, 0
        stat = os.stat(FILENAME)
        return stat.st_mtime, stat.st_size
    except OSError as e:
        # Excel often locks the file during save, this is expected
        return None, None

def watch_file():
    global last_mtime
    try:
        last_mtime, last_size = get_file_info()
        if last_mtime is None: last_mtime, last_size = 0, 0
        
        print(f"[*] Watching for changes in: {FILENAME}")
        
        while True:
            time.sleep(POLL_INTERVAL)
            curr_mtime, curr_size = get_file_info()
            
            if curr_mtime is None: continue # Skip if file locked
            
            if curr_mtime > last_mtime or curr_size != last_size:
                print(f"[!] Change detected. Waiting for file to stabilize...")
                
                # Wait for file to stop changing (essential for large 80MB files)
                stable_count = 0
                while stable_count < 3:
                    time.sleep(1.0)
                    check_info = get_file_info()
                    if check_info == (None, None): continue
                    
                    check_mtime, check_size = check_info
                    if check_mtime == curr_mtime and check_size == curr_size:
                        stable_count += 1
                    else:
                        curr_mtime, curr_size = check_mtime, check_size
                        stable_count = 0
                
                print(f"[*] File stabilized. Processing data (this may take 2 mins for 80MB)...")
                time.sleep(2) # Stabilization
                
                # Run processor in background to not block the watcher loop, 
                # though here we can probably block briefly or use a flag.
                global is_processing, cached_data, current_status
                is_processing = True
                notify_clients("processing", "Starting high-speed read...")
                
                try:
                    def progress_cb(msg):
                        notify_clients("progress", msg)
                    
                    new_data = process_excel_data(FILENAME, progress_cb)
                    if new_data:
                        cached_data = new_data
                        last_mtime = curr_mtime
                        notify_clients("update", "Dashboard Updated")
                    else:
                        notify_clients("error_msg", "Excel Processing Failed")
                finally:
                    is_processing = False
                    current_status = "Live Sync Ready"
    except Exception as e:
        print(f"[ERROR] Watcher thread crashed: {e}")
        traceback.print_exc()

def notify_clients(event_type, msg=None):
    global current_status
    if msg: current_status = msg
    
    dead_clients = []
    for q in clients:
        try:
            if msg:
                q.put(f"event: {event_type}\ndata: {msg}\n\n")
            else:
                q.put(f"event: {event_type}\ndata: {json.dumps({'ts':time.time()})}\n\n")
        except:
            dead_clients.append(q)
    for q in dead_clients:
        if q in clients: clients.remove(q)

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
        try:
            # Safely check the log message for dashboard updates
            msg = format % args if args else format
            if "GET /latest" in msg:
                print(f"[*] Dashboard data requested.")
        except:
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
        try:
            # Normalize path for matching
            clean_path = self.path.split('?')[0].rstrip('/')
            
            if clean_path == '/events':
                self.handle_sse()
            elif clean_path == '/latest':
                self.handle_latest()
            elif clean_path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
            else:
                # Serve static files as usual
                super().do_GET()
        except Exception as e:
            print(f"[ERROR] Request handler failed: {e}")
            traceback.print_exc()

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
            print(f"[+] Dashboard connected (Total: {len(clients)})")
            
            # Keep connection open
            while True:
                # Send keep-alive every 30 seconds to prevent timeout
                time.sleep(30)
                sse.send_event("ping", "keep-alive")
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass # Normal disconnection
        except Exception as e:
            print(f"[!] SSE Connection error: {e}")
        finally:
            if 'sse' in locals() and sse in clients:
                clients.remove(sse)
            print(f"[-] Dashboard disconnected.")

    def handle_latest(self):
        global cached_data, is_processing
        
        if is_processing:
            self.send_response(202) # Accepted, but still processing
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "processing"}).encode('utf-8'))
            return

        if cached_data is None:
            # First run or missing data, try to process now
            print("[*] Cache empty. Processing file for the first time...")
            cached_data = process_excel_data(FILENAME)
            
        if cached_data is None:
            self.send_error(503, "Data not available and failed to process")
            return

        try:
            content = json.dumps(cached_data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(content)
            print(f"[*] Served pre-processed JSON to dashboard ({len(content)/1024:.1f} KB).")
        except Exception as e:
            print(f"[ERROR] handle_latest failed: {e}")
            traceback.print_exc()
            self.send_error(500, "Internal Server Error")

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    
    def handle_error(self, request, client_address):
        # Suppress the scary tracebacks for normal browser disconnections
        pass

def run_server():
    try:
        with ThreadingTCPServer(("", PORT), DashboardHandler) as httpd:
            print(f"[*] Live Sync Server Active on http://localhost:{PORT}")
            print(f"[*] Watching: {FILENAME}")
            # Automatically open the dashboard
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            httpd.serve_forever()
    except Exception as e:
        print(f"[ERROR] Server crashed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Start watcher thread
    watcher_thread = threading.Thread(target=watch_file, daemon=True)
    watcher_thread.start()
    
    # Start server
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
    except Exception as e:
        print(f"[FATAL] App crashed: {e}")
        traceback.print_exc()
