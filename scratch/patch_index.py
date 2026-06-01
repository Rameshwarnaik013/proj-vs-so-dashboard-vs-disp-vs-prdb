import sys
import os

filepath = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Topbar
old_topbar = """      <div class="topbar-left">
        <div class="status-dot"></div>
        <span class="status-text">Live Server Connected</span>
        <span class="records-badge" id="records-badge">— records</span>
        <span class="unit-badge">Qty</span>
      </div>"""

new_topbar = """      <div class="topbar-left">
        <div class="status-dot"></div>
        <span class="status-text">Live Server: Connecting...</span>
        <span class="records-badge" id="records-badge">Syncing...</span>
        <span class="unit-badge">Metric: Kg/Qty</span>
      </div>"""

if old_topbar in content:
    content = content.replace(old_topbar, new_topbar)
    print("Topbar updated.")
else:
    # Try with line numbers or slightly different whitespace if it fails
    print("Warning: Could not find exact Topbar match.")

# 2. Update initLiveSync
# We'll use a more surgical replacement for the function body
import re

func_pattern = r"function initLiveSync\(\) \{.*?es\.addEventListener\('update', async \(e\) => \{.*?\}\);\s+core\(\);\s+\}"
# That regex is too complex. Let's just find the start and end of the function.

start_marker = "function initLiveSync() {"
end_marker = "connect();\n}"

# Find the indices
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx != -1 and end_idx != -1:
    new_func = """function initLiveSync() {
  const statusDot = document.querySelector('.status-dot');
  const statusText = document.querySelector('.status-text');
  
  const connect = () => {
    const es = new EventSource('/events');
    
    es.onopen = () => {
      statusDot.style.background = '#10B981';
      statusText.innerText = 'Live Excel Sync: Active';
    };
    
    es.onerror = () => {
      statusDot.style.background = '#6B7280';
      statusText.innerText = 'Live Sync: Offline';
      es.close();
      setTimeout(connect, 5000);
    };

    es.addEventListener('processing', () => {
      statusDot.style.background = '#F59E0B'; // Orange
      statusText.innerText = 'Live Sync: Processing 80MB Excel...';
    });
    
    es.addEventListener('update', async (e) => {
      console.log('Live Update Received. Fetching pre-processed JSON...');
      try {
        const response = await fetch('/latest?t=' + Date.now());
        const newData = await response.json();
        
        if (newData.status === 'processing') {
            statusDot.style.background = '#F59E0B';
            statusText.innerText = 'Live Sync: Still Processing...';
            return;
        }

        // Critical: Update global DATA and re-render
        DATA = newData;
        activeFilters = {}; 
        console.log('Live Sync: Global DATA updated via Backend. Re-rendering...');
        
        buildFilters();
        renderAll();
        
        const badge = document.getElementById('records-badge');
        if (badge) badge.innerText = 'Active (JSON Sync)';
        
        statusDot.style.background = '#10B981';
        statusText.innerText = 'Live Excel Sync: Updated';
        statusDot.style.transform = 'scale(1.5)';
        setTimeout(() => {
            statusDot.style.transform = 'scale(1)';
            statusText.innerText = 'Live Excel Sync: Active';
        }, 1000);
      } catch (err) {
        console.error('Live Sync: Error fetching JSON:', err);
        statusText.innerText = 'Live Sync: Process Error';
      }
    });

    es.addEventListener('error_msg', (e) => {
        statusText.innerText = 'Live Sync: Excel Error';
        statusDot.style.background = '#EF4444';
    });
  };
  
  connect();
}"""
    content = content[:start_idx] + new_func + content[end_idx + len(end_marker):]
    print("initLiveSync function updated.")
else:
    print(f"Error: Could not find initLiveSync function markers. Start: {start_idx}, End: {end_idx}")

# 3. Update getSparkline
gs_start = "function getSparkline(name, metricKey) {"
gs_end = "return MONTH_ORDER.map(m => (dd[name][m] || {})[metricKey] || 0);\n}"

s3 = content.find(gs_start)
e3 = content.find(gs_end, s3)

if s3 != -1 and e3 != -1:
    new_gs = """function getSparkline(name, metricKey) {
  // Get monthly data for this name from dim_data
  const dimKey = activeDim;
  const dd = DATA.dim_data[dimKey];
  if (!dd || !dd[name]) return MONTHS.map(()=>0);
  return MONTHS.map(m => (dd[name][m] || {})[metricKey] || 0);
}"""
    content = content[:s3] + new_gs + content[e3 + len(gs_end):]
    print("getSparkline function updated.")
else:
    print(f"Error: Could not find getSparkline markers. Start: {s3}, End: {e3}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patching complete.")
