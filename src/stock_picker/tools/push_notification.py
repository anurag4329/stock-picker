import os

import requests
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class PushNotificationToolInput(BaseModel):
    """Input schema for PushNotificationTool."""
    message: str = Field(..., description="The message to be sent to the user.")

class PushNotificationTool(BaseTool):
    name: str = "Send a push notification"
    description: str = (
        "This tool is used to send a push notification to the user."
    )
    args_schema: Type[BaseModel] = PushNotificationToolInput

    def _run(self, message: str) -> str:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": message,
            },
        )

        return '{"Notification sent": true}'
