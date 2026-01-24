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
        self.worker_url = os.getenv("CLOUD_TASKS_WORKER_URL")
        self.worker_sa_email = os.getenv("CLOUD_TASKS_WORKER_SA_EMAIL")

        if not all([self.project, self.location, self.queue, self.worker_url, self.worker_sa_email]):
            raise ValueError("Missing required environment variables for CloudTasksService.")

        self.parent = self.client.queue_path(self.project, self.location, self.queue)

    def create_save_result_task(self, geojson_data: Dict, analysis_type: str, request_bbox: List[float]):
        """
        Creates a Cloud Task to save analysis results asynchronously.
        """
        payload = {
            "geojson_data": geojson_data,
            "analysis_type": analysis_type,
            "request_bbox": request_bbox
        }

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{self.worker_url}/tasks/save-results",
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