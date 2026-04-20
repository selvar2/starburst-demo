"""Keep Starburst free cluster alive by pinging every 1 minute."""

import time
from datetime import datetime
from pathlib import Path
from starburst_client import StarburstClient

client = StarburstClient()
INTERVAL = 60  # 1 minute
TRIM_INTERVAL = 300  # 5 minutes
KEEP_LINES = 10
LOG_FILE = Path(__file__).parent / "keepalive.log"

ping_count = 0

while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        result = client.execute('SELECT 1 AS result')
        msg = f"[{ts}] OK - {result.get('rows', [])}\n"
    except Exception as e:
        msg = f"[{ts}] ERROR - {e}\n"
        client._conn = None
    with open(LOG_FILE, "a") as f:
        f.write(msg)
    print(msg.strip(), flush=True)

    ping_count += 1

    # Every 5 minutes (5 pings), trim log to last 10 entries
    if ping_count % (TRIM_INTERVAL // INTERVAL) == 0:
        try:
            lines = LOG_FILE.read_text().splitlines()
            if len(lines) > KEEP_LINES:
                LOG_FILE.write_text("\n".join(lines[-KEEP_LINES:]) + "\n")
        except Exception:
            pass

    time.sleep(INTERVAL)
