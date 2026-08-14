import asyncio
import json
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.deps import get_db

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Fetch Company Library
        print("Fetching projects...")
        response = await client.get("/api/v1/projects")
        projects = response.json()
        
        target = None
        for p in projects:
            if "Valentine" in p["title"]:
                target = p
                break
                
        if not target:
            print("ERROR: F#K Valentine's Day not found in Project Library.")
            return
            
        project_id = target["id"]
        print(f"Found Target Project: {target['title']} ({project_id})")
        
        # 2. Run real screenplay through SA-1 parser
        print("\nTriggering SA-1 Parser...")
        response = await client.post(f"/api/v1/script-analysis/projects/{project_id}/parse")
        if response.status_code != 200:
            print(f"ERROR: Parse failed: {response.text}")
            return
        parse_result = response.json()
        print(f"Parse Result: {parse_result}")
        
        # 3. Check Script State
        print("\nFetching Script State...")
        response = await client.get(f"/api/v1/script-analysis/projects/{project_id}/script")
        script_state = response.json()
        print(f"Script State: {script_state['status']}")
        
        # 4. Check Canonical State
        print("\nFetching Canonical State...")
        response = await client.get(f"/api/v1/script-analysis/projects/{project_id}/state")
        canonical_state = response.json()
        print(f"Readiness: {canonical_state['readiness']}")
        
        # 5. Fetch Optimizer Input
        print("\nFetching Optimizer Input...")
        response = await client.get(f"/api/v1/script-analysis/projects/{project_id}/optimizer-input")
        optimizer_input = response.json()
        print(f"Optimizer Input Readiness: {optimizer_input['readiness']}")
        
        # Save Calibration Fixture
        fixture = {
            "parse_result": parse_result,
            "script_state": script_state,
            "canonical_state": canonical_state,
            "optimizer_input": optimizer_input,
        }
        
        fixture_path = "../../docs/validation/SCRIPT_ANALYZER_REAL_BUDGET_FIXTURE_001.json"
        with open(fixture_path, "w") as f:
            json.dump(fixture, f, indent=2)
            
        print(f"\nSaved fixture to {fixture_path}")

if __name__ == "__main__":
    asyncio.run(main())
