import os
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import datetime
from typing import Dict, List

class CloudTasksService:
    def __init__(self):
        self.client = tasks_v2.CloudTasksClient()
        self.project = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_REGION")
        self.queue = os.getenv("CLOUD_TASKS_QUEUE")
        
        # Helper method for defaults
        self.worker_sa_email = os.getenv("CLOUD_TASKS_WORKER_SA_EMAIL")

        # Load Worker URLs for Microservices
        self.worker_urls = {
            "default": os.getenv("CLOUD_TASKS_WORKER_URL"), # Fallback
            "landcover": os.getenv("WORKER_URL_LANDCOVER"),
            "failles": os.getenv("WORKER_URL_DETECTION"),
            "mines": os.getenv("WORKER_URL_MINERALS"),
            "minéraux": os.getenv("WORKER_URL_MINERALS"),
            "glissements de terrain": os.getenv("WORKER_URL_DETECTION") # Using detection worker for consistency
        }

        if not all([self.project, self.location, self.queue, self.worker_sa_email]):
             # We might not have all worker URLs at build time, but we need the basics
             raise ValueError("Missing required basic environment variables for CloudTasksService.")

        self.parent = self.client.queue_path(self.project, self.location, self.queue)

    def create_task(self, endpoint: str, payload: Dict):
        """
        Creates a generic Cloud Task, routing to the correct service based on analysis_type.
        """
        analysis_type = payload.get("analysis_type")
        # Get the right worker URL based on analysis type
        target_url_base = self.worker_urls.get(str(analysis_type).lower())
        
        if not target_url_base or target_url_base.lower() == "none":
            print(f"⚠️ Worker for {analysis_type} is not available. Attempting fallback to default worker.")
            # Fallback to general worker if possible, or raise error
            target_url_base = self.worker_urls.get("default")
            if not target_url_base or target_url_base.lower() == "none":
                raise ValueError(f"No worker URL available for analysis type: {analysis_type} and default worker is also unavailable.")
        
        if not target_url_base: # This check is redundant if the above logic is correct, but kept for safety
            raise ValueError(f"No worker URL configured for analysis type: {analysis_type}")

        full_url = f"{target_url_base}{endpoint}"

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": full_url,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
                "oidc_token": {"service_account_email": self.worker_sa_email},
            },
             "dispatch_deadline": datetime.timedelta(minutes=15).total_seconds(), # 15 min for analysis
        }

        response = self.client.create_task(parent=self.parent, task=task)
        print(f"Created task {response.name} targeting {full_url}")
        return response.name

    def create_save_result_task(self, geojson_data: Dict, analysis_type: str, request_bbox: List[float]):
        """
        Creates a Cloud Task to save analysis results asynchronously.
        """
        payload = {
            "geojson_data": geojson_data,
            "analysis_type": analysis_type,
            "request_bbox": request_bbox
        }
        
        # Save results can go to the Router or a specific worker. 
        # Using default/router URL usually fine as it's just DB write.
        target_url = self.worker_urls.get("default")
        if not target_url: 
             # Fallback: try to find any available URL
             target_url = next((url for url in self.worker_urls.values() if url), None)

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target_url}/tasks/save-results",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
                "oidc_token": {"service_account_email": self.worker_sa_email},
            },
            # --- Configuration de la politique de retry ---
            # Temps maximum accordé au worker pour terminer la tâche.
            "dispatch_deadline": datetime.timedelta(minutes=5).total_seconds(),
            # Nombre maximum de tentatives en cas d'échec.
            "max_dispatches": 5,
            # Temps minimum d'attente avant une nouvelle tentative.
            "min_backoff": datetime.timedelta(seconds=10).total_seconds(),
        }

        response = self.client.create_task(parent=self.parent, task=task)
        print(f"Created task: {response.name}")