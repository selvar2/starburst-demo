"""Keep Starburst free cluster alive by pinging every 4 minutes."""

import time
from datetime import datetime
from pathlib import Path
from starburst_client import StarburstClient

client = StarburstClient()
INTERVAL = 240  # 4 minutes
LOG_FILE = Path(__file__).parent / "keepalive.log"

while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        result = client.execute('SELECT id FROM mcp2ohio.test_writes.demo LIMIT 1')
        msg = f"[{ts}] OK - {result.get('rows', [])}\n"
    except Exception as e:
        msg = f"[{ts}] ERROR - {e}\n"
        client._conn = None
    with open(LOG_FILE, "a") as f:
        f.write(msg)
    print(msg.strip(), flush=True)
    time.sleep(INTERVAL)
