MANIFEST_CONTENT = """{
  "name": "mn10 Anomaly Alert", "short_name": "Anomaly System", "start_url": "/",
  "display": "standalone", "background_color": "#111827", "theme_color": "#dc2626",
  "icons":[{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}]
}"""

SW_CONTENT = "self.addEventListener('install', (e) => { self.skipWaiting(); }); self.addEventListener('activate', (e) => { return self.clients.claim(); });"

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#dc2626"/><path d="M50 20 L50 60 M50 75 L50 80" stroke="white" stroke-width="10" stroke-linecap="round"/></svg>"""

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Anomaly Dashboard</title> <link rel="manifest" href="/manifest.json">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-900 text-gray-100 font-sans antialiased min-h-screen">
    <div class="max-w-4xl mx-auto p-4 sm:p-6">
        <div class="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
            <h1 class="text-2xl font-bold text-red-500"><i class="fa-solid fa-shield-halved mr-2"></i> Anomaly Monitor</h1>
            <button id="notifyBtn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow">
                <i class="fa-solid fa-bell"></i> Enable Notifications
            </button>
        </div>
        <div class="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-700 bg-gray-850">
                <h2 class="text-xl font-semibold"><i class="fa-solid fa-list mr-2"></i> Recent Incident Logs</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left" id="logsTable">
                    <thead class="bg-gray-700 text-gray-300">
                        <tr>
                            <th class="px-6 py-3">Time</th> <th class="px-6 py-3">Event</th>
                            <th class="px-6 py-3">Score</th> <th class="px-6 py-3">Evidence (30s)</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-700" id="logsBody">
                        <tr><td colspan="4" class="px-6 py-4 text-center text-gray-400">Loading records...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
        const notifyBtn = document.getElementById('notifyBtn');
        function updateNotifyBtn() {
            if (Notification.permission === 'granted') {
                notifyBtn.classList.replace('bg-blue-600', 'bg-green-600');
                notifyBtn.innerHTML = '<i class="fa-solid fa-bell-slash"></i> Notifications Active';
            }
        }
        notifyBtn.addEventListener('click', async () => {
            let perm = await Notification.requestPermission();
            if (perm === 'granted') { updateNotifyBtn(); new Notification('Alerts Enabled!', { icon: '/icon.svg' }); } 
            else { alert('Permission denied.'); }
        });
        updateNotifyBtn();

        function createRow(log) {
            return `
                <tr class="hover:bg-gray-750 transition-colors animate-pulse-once">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${log.timestamp}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-red-400">${log.detected_class}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${parseFloat(log.confidence_score).toFixed(2)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <audio controls preload="none" class="h-8 w-48 outline-none bg-gray-800 rounded">
                            <source src="${log.audio_url}" type="audio/ogg">
                        </audio>
                    </td>
                </tr>`;
        }

        fetch('/api/logs').then(res => res.json()).then(data => {
            const tbody = document.getElementById('logsBody'); tbody.innerHTML = '';
            if(data.logs.length === 0) tbody.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-4">No anomalies detected yet.</td></tr>';
            data.logs.forEach(log => { tbody.innerHTML += createRow(log); });
        });

        const evtSource = new EventSource("/api/stream");
        evtSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const tbody = document.getElementById('logsBody');
            if (tbody.querySelector('.text-center')) tbody.innerHTML = '';
            tbody.insertAdjacentHTML('afterbegin', createRow(data));
            if (tbody.children.length > 50) tbody.lastElementChild.remove();

            if (Notification.permission === 'granted') {
                navigator.serviceWorker.ready.then(reg => {
                    reg.showNotification('Anomaly Detected!', {
                        body: `Score: ${data.confidence_score}\\nTime: ${data.timestamp}`,
                        icon: '/icon.svg', vibrate: [200, 100, 200]
                    });
                });
            }
        };
    </script>
</body>
</html>"""
