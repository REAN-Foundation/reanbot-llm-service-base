import os
import httpx

class AnalyticsService:

    @staticmethod
    async def push_event(event: dict):
        try:
            base_url = os.getenv("ANALYTICS_API_BASE_URL")
            api_key = os.getenv("INTERNAL_API_KEY")

            if not base_url or not api_key:
                print("Analytics config missing")
                return

            url = f"{base_url}/events/"

            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=event, headers=headers)
                print("response body:", response.text)

        except Exception as e:
            print("Analytics push failed:", str(e))