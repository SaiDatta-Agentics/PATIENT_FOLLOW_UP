import asyncio
from app.core.config import settings

class CommunicationService:
    def _simulated(self):
        return not settings.AZURE_COMMUNICATION_CONNECTION_STRING

    async def send_sms(self, to: str, message: str) -> dict:
        if self._simulated() or not settings.AZURE_SMS_FROM_NUMBER:
            return {"status": "SIMULATED", "message_id": "demo-sms", "provider": "DEMO"}
        from azure.communication.sms.aio import SmsClient
        client = SmsClient.from_connection_string(settings.AZURE_COMMUNICATION_CONNECTION_STRING)
        result = await client.send(from_=settings.AZURE_SMS_FROM_NUMBER, to=[to], message=message)
        item = result[0]
        return {"status": "SENT" if item.successful else "FAILED", "message_id": item.message_id, "provider": "AZURE_COMMUNICATION_SERVICES"}

    async def start_voice_call(self, to: str) -> dict:
        if self._simulated() or not settings.AZURE_CALLER_ID or not settings.AZURE_CALL_CALLBACK_URL:
            return {"status": "SIMULATED", "message_id": "demo-call", "provider": "DEMO"}
        from azure.communication.callautomation.aio import CallAutomationClient
        from azure.communication.callautomation import PhoneNumberIdentifier
        client = CallAutomationClient.from_connection_string(settings.AZURE_COMMUNICATION_CONNECTION_STRING)
        result = await client.create_call(
            target_participant=PhoneNumberIdentifier(to),
            callback_url=settings.AZURE_CALL_CALLBACK_URL,
            source_caller_id_number=PhoneNumberIdentifier(settings.AZURE_CALLER_ID),
        )
        return {"status": "INITIATED", "message_id": result.call_connection_id, "provider": "AZURE_COMMUNICATION_SERVICES"}

communication_service = CommunicationService()
