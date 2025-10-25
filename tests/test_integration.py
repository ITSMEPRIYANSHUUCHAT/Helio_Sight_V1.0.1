import pytest
import requests
import psycopg2
from contextlib import contextmanager
from testcontainers.compose import DockerCompose  # Handles your compose.yml
import time  # For manual wait if needed

# Session-wide fixture: Starts compose via context manager, waits for readiness, yields services, then tears down automatically
@pytest.fixture(scope="session")
def compose_services():
    print("🚀 Starting Docker Compose...")
    # Path to your compose file (adjust if not in project root)
    compose = DockerCompose(
        ".",  # Current directory
        compose_file_name="docker-compose.yml",
        build=False,  # Skip rebuild for speed (pre-build manually if needed)
        pull=False   # Skip pulls
    )
    
    with compose:  # Starts services (implicit up), yields, then down on exit
        print("⏳ Pinging FastAPI readiness...")
        # Manual wait for FastAPI (faster than compose.wait_for)
        max_tries = 20  # ~40s max
        for _ in range(max_tries):
            try:
                resp = requests.get("http://localhost:8000/health", timeout=2)
                if resp.status_code == 200:
                    break
            except:
                pass
            time.sleep(2)
        else:
            raise TimeoutError("FastAPI not ready")
        print("✅ FastAPI ready!")
        
        # Quick DB ping
        with get_db_connection({
            "postgres_host": "localhost", "postgres_port": 5432,
            "postgres_db": "solar_db", "postgres_user": "postgres", "postgres_password": "password"
        }) as conn:
            print("✅ DB ready!")
        
        yield {
            "fastapi_url": "http://localhost:8000",
            "postgres_host": "localhost",
            "postgres_port": 5432,
            "postgres_db": "solar_db",
            "postgres_user": "postgres",
            "postgres_password": "password",
        }

# Helper: Postgres connection context manager
@contextmanager
def get_db_connection(services):
    conn = psycopg2.connect(
        host=services["postgres_host"],
        port=services["postgres_port"],
        dbname=services["postgres_db"],
        user=services["postgres_user"],
        password=services["postgres_password"]
    )
    try:
        yield conn
    finally:
        conn.close()

def test_full_api_credential_flow(compose_services):
    base_url = compose_services["fastapi_url"]
    headers = {"Content-Type": "application/json"}
    
    print("🔑 Logging in...")
    # Use /auth/login as per your endpoints
    login_payload = {"username": "demo", "password": "demo_pass"}  # Adjust creds if needed (e.g., "demo"/"demo")
    login_resp = requests.post(f"{base_url}/auth/login", json=login_payload, headers=headers)
    print(f"Login response: {login_resp.status_code} - {login_resp.text[:200]}...")  # Debug body
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    token = token_data["access_token"]  # Standard JWT key
    auth_header = {"Authorization": f"Bearer {token}"}
    print("✅ Token acquired!")
    
    # Step 3: Create Customer (if none) - Check /customers/ first
    print("👥 Listing customers...")
    customers_resp = requests.get(f"{base_url}/customers/", headers=auth_header)
    print(f"Customers list: {customers_resp.status_code} - {customers_resp.text[:100]}...")
    assert customers_resp.status_code == 200
    customers = customers_resp.json()
    
    customer_id = None
    if not customers:  # Empty list
        print("🆕 Creating customer...")
        create_cust_payload = {"name": "Test Customer", "email": "test@example.com"}  # Adjust to CustomerCreate schema
        create_cust_resp = requests.post(
            f"{base_url}/customers/create",
            json=create_cust_payload,
            headers={**headers, **auth_header}
        )
        print(f"Create customer: {create_cust_resp.status_code} - {create_cust_resp.text[:100]}...")
        assert create_cust_resp.status_code == 201  # Or 200 per your spec
        customer_id = create_cust_resp.json()["id"]  # Adjust key (e.g., "customer_id")
    else:
        customer_id = customers[0]["id"]  # Use first existing
    assert customer_id, "No customer_id obtained"
    print(f"✅ Customer ID: {customer_id}")
    
    print("📝 Creating API Credential...")
    cred_payload = {
        "customer_id": customer_id,
        "api_provider": "solarman",
        "username": "solar_user",
        "password": "solar_pass",
        "api_key": "key123",
        "api_secret": "secret123"
    }  # Adjust to ApiCredentialCreate if extra fields
    create_cred_resp = requests.post(
        f"{base_url}/api-credentials/create",
        json=cred_payload,
        headers={**headers, **auth_header}
    )
    print(f"/api-credentials/create: {create_cred_resp.status_code} - {create_cred_resp.text[:100]}...")
    assert create_cred_resp.status_code == 200
    created_cred = create_cred_resp.json()
    assert "id" in created_cred
    print("✅ Credential created!")
    
    print("📋 Listing Credentials...")
    list_resp = requests.get(f"{base_url}/api-credentials/", headers=auth_header)
    print(f"List: {list_resp.status_code} - {len(list_resp.json())} items")
    assert list_resp.status_code == 200
    creds_list = list_resp.json()
    assert len(creds_list) >= 1
    assert any(cred["api_provider"] == "solarman" for cred in creds_list)
    print("✅ List verified!")
    
    print("🗄️ DB Verification...")
    with get_db_connection(compose_services) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM api_credentials;")
            result = cur.fetchone()
            assert result is not None
            row_count = result[0]
            assert row_count == 1  # Assuming clean state; adjust if multiples
            cur.execute("SELECT api_provider FROM api_credentials;")
            provider = cur.fetchone()[0]
            assert provider == "solarman"
    print("✅ DB check passed!")