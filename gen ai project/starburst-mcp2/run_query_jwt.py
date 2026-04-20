"""Run a query against Starburst Galaxy using the headless JWT/OAuth client."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from starburst_client_jwt import StarburstClientJWT

client = StarburstClientJWT()
print(f"Connecting to {client.host} (catalog={client.catalog}, auth={client.auth_mode})")
print(f"Galaxy portal: {client.galaxy_host}")
print(f"Email: {client.email}")
print()

query = 'SELECT * FROM "sample"."burstbank"."account" LIMIT 1'
print(f"Executing: {query}")
print()

result = client.execute(query)

columns = result["columns"]
rows = result["rows"]
print(f"{len(rows)} row(s) returned.\n")

# Print header
header = " | ".join(str(c).ljust(10) for c in columns)
print(header)
print("-" * len(header))
for row in rows:
    print(" | ".join(str(v).ljust(10) for v in row))
