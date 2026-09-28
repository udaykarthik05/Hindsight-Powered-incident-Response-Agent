"""
Standalone verification script for Hindsight connectivity.

Usage:
    python -m app.hindsight.verify
"""

import asyncio
import sys
from app.core.config import get_settings
from app.hindsight.client import HindsightClientManager


async def verify_connectivity() -> bool:
    settings = get_settings()
    manager = HindsightClientManager(settings)

    print("=" * 70)
    print(" HINDSIGHT CONNECTIVITY VERIFICATION")
    print("=" * 70)
    print(f"Target Base URL : {settings.hindsight_base_url}")
    print(f"Target Bank ID  : {settings.hindsight_bank_id}")
    print(f"API Key Set     : {'Yes (Masked)' if settings.hindsight_api_key else 'No (None)'}")
    print(f"Timeout         : {settings.hindsight_timeout}s")
    print("-" * 70)
    print("Probing Hindsight server status...")

    status = await manager.check_connection()
    await manager.close()

    print("-" * 70)
    if status.connected:
        print(" STATUS: [CONNECTED]")
        print(f"  Server Version: {status.server_version}")
        print(f"  Message       : {status.message}")
        print("=" * 70)
        print("Hindsight is ready for incident memory operations (RETAIN, RECALL, REFLECT).")
        return True
    else:
        print(" STATUS: [DISCONNECTED / UNREACHABLE]")
        print(f"  Error Details : {status.error}")
        print(f"  Diagnosis     : {status.message}")
        print("=" * 70)
        print("\nNext Steps to Enable Hindsight:")
        print("  1. For Local Docker Instance:")
        print("     Run: docker run -d -p 8888:8888 -p 5432:5432 vectorize/hindsight:latest")
        print("     Ensure HINDSIGHT_BASE_URL=http://localhost:8888 in .env")
        print("  2. For Hindsight Cloud:")
        print("     Set HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io")
        print("     Set HINDSIGHT_API_KEY=<your-api-key> in .env")
        print("\nNote: Integration code is fully ready and configured.")
        return False


def main() -> None:
    success = asyncio.run(verify_connectivity())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
