import sys
import os

filepath = r"c:\Users\Admin\OneDrive - https farmley.com\Desktop\FINAL_01\index.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initLiveSync with Retry Logic
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

    es.addEventListener('processing', () => {
      statusDot.style.background = '#F59E0B'; // Orange
      statusText.innerText = 'Live Sync: Processing...';
    });
    
    es.addEventListener('update', async (e) => {
      console.log('Live Update Received. Fetching pre-processed JSON...');
      
      const fetchLatest = async (retryCount = 0) => {
        try {
          const response = await fetch('/latest?t=' + Date.now());
          const newData = await response.json();
          
          if (newData.status === 'processing') {
              const waitTime = 10;
              statusDot.style.background = '#F59E0B';
              statusText.innerText = `Sync: Still Processing... (Retry ${retryCount + 1})`;
              console.log(`Backend is busy. Retrying in ${waitTime}s...`);
              setTimeout(() => fetchLatest(retryCount + 1), waitTime * 1000);
              return;
          }

          // Critical: Update global DATA and re-render
          DATA = newData;
          activeFilters = {}; 
          console.log('Live Sync: Global DATA updated via Backend. Re-rendering...');
          
          buildFilters();
          renderAll();
          
          // Force hide loading screen if it's there
          const loader = document.getElementById('loading');
          if (loader) loader.classList.add('hidden');
          
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
          statusText.innerText = 'Live Sync: Connection Reset';
          // Try again in 5s if fetch failed entirely
          setTimeout(() => fetchLatest(retryCount + 1), 5000);
        }
      };

      fetchLatest();
    });

    es.addEventListener('error_msg', (e) => {
        statusText.innerText = 'Live Sync: Excel Error';
        statusDot.style.background = '#EF4444';
    });
  };
  
  connect();
}"""
    content = content[:start_idx] + new_func + content[end_idx + len(end_marker):]
    print("initLiveSync with retry logic patched.")
else:
    print(f"Error: Could not find initLiveSync function markers. Start: {start_idx}, End: {end_idx}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patching complete.")
