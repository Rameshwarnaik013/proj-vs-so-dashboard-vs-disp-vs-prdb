import sys
import os

filepath = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initLiveSync with Progress Handling
start_marker = "function initLiveSync() {"
end_marker = "connect();\n}"

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

    es.addEventListener('processing', (e) => {
      statusDot.style.background = '#F59E0B'; // Orange
      statusText.innerText = e.data || 'Live Sync: Processing...';
    });

    es.addEventListener('progress', (e) => {
      statusDot.style.background = '#F59E0B';
      statusText.innerText = 'Live Sync: ' + e.data;
    });
    
    es.addEventListener('update', async (e) => {
      console.log('Live Update Received. Fetching pre-processed JSON...');
      
      const fetchLatest = async (retryCount = 0) => {
        try {
          const response = await fetch('/latest?t=' + Date.now());
          const newData = await response.json();
          
          if (newData.status === 'processing') {
              const waitTime = 5;
              statusDot.style.background = '#F59E0B';
              statusText.innerText = `Sync: Busy... (Retry in ${waitTime}s)`;
              setTimeout(() => fetchLatest(retryCount + 1), waitTime * 1000);
              return;
          }

          DATA = newData;
          activeFilters = {}; 
          console.log('Live Sync: Global DATA updated. Re-rendering...');
          
          buildFilters();
          renderAll();
          
          const loader = document.getElementById('loading');
          if (loader) loader.classList.add('hidden');
          
          const badge = document.getElementById('records-badge');
          if (badge) badge.innerText = 'Active (JSON Sync)';
          
          statusDot.style.background = '#10B981';
          statusText.innerText = 'Live Excel Sync: Updated';
          setTimeout(() => {
              statusText.innerText = 'Live Excel Sync: Active';
          }, 2000);
        } catch (err) {
          console.error('Live Sync: Error fetching JSON:', err);
          statusText.innerText = 'Live Sync: Connection Reset';
          setTimeout(() => fetchLatest(retryCount + 1), 5000);
        }
      };

      fetchLatest();
    });

    es.addEventListener('error_msg', (e) => {
        statusText.innerText = 'Live Sync: ' + e.data;
        statusDot.style.background = '#EF4444';
    });
  };
  
  connect();
}"""
    content = content[:start_idx] + new_func + content[end_idx + len(end_marker):]
    print("initLiveSync with progress tracking patched.")
else:
    print(f"Error: Could not find initLiveSync markers.")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patching complete.")
