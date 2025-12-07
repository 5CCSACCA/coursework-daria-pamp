import requests
import sys

# URL of our Gateway API
BASE_URL = "http://localhost:8080"

def test_health_check():
    """Stage 10: Verify the system is reachable"""
    print(f"Testing connection to {BASE_URL}...")
    try:
        # Check if the docs page loads (means server is up)
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API is reachable (Status 200)")
        else:
            print(f"❌ API returned status {response.status_code}")
            sys.exit(1)
            
        # Check Monitoring endpoint (Stage 9)
        metrics = requests.get(f"{BASE_URL}/metrics")
        if metrics.status_code == 200:
            print("✅ Monitoring endpoint (/metrics) is active")
        else:
            print("❌ Monitoring failed")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_health_check()
    print("\nSUCCESS: System basic health verified.")
