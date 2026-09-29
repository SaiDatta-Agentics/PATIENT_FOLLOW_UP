# SaiDatta CareFlow AI — Patient Follow-Up & Recall Agent v3

A real-time dental follow-up agent that runs immediately with rich demo data and uses the **same workflow for newly entered real patient data**.

## What changed in v3

- Two workspace experiences only:
  - **Patient Care workspace** — one patient sees only their care plan, chat and appointments.
  - **Clinic Operations workspace** — doctors and staff see the shared patient queue, live agent activity, escalations and schedule.
- Working **Create account** flow.
  - Patient signup creates or links a patient profile.
  - Doctor/staff signup requires `CLINIC_ACCESS_CODE`.
- Working patient care chat with persisted conversations.
- Appointment intent returns real selectable demo slots; clicking a slot creates a confirmed appointment.
- Symptom/fee/human requests create staff escalations.
- WebSocket live-update channel plus periodic fallback refresh.
- Automated follow-up worker processes due tasks in the background.
- 12 seeded demo patients covering due, overdue, contacted, responded, booked, escalated, no-response and completed states.
- New patients entered by clinic staff automatically get a follow-up task; blank follow-up time defaults to about one minute so automation is easy to demonstrate.
- Azure OpenAI, Azure Communication Services, Azure PostgreSQL, Azure Blob Storage and Azure Container Apps configuration remains included.

## Demo credentials

| Workspace | Username | Password |
|---|---|---|
| Doctor | `drjones` | `doctor123` |
| Staff | `staff1` | `staff123` |
| Patient | `john` | `patient123` |
| Patient | `maria` | `patient123` |
| Patient | `priya` | `patient123` |

Doctor/staff demo registration access code: `CLINIC-DEMO`.

## Local run — Windows PowerShell

### Backend

```powershell
cd C:\Users\YOUR_NAME\Downloads\saidatta-patient-followup-agent-v3\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item ..\.env.example .\.env
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Health check:

```text
http://localhost:8001/api/health
```

API docs:

```text
http://localhost:8001/docs
```

### Frontend

Open a second PowerShell window:

```powershell
cd C:\Users\YOUR_NAME\Downloads\saidatta-patient-followup-agent-v3\frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Vite proxies `/api` and the WebSocket connection to FastAPI on port `8001`.

## Fast demo

1. Sign in as `staff1 / staff123`.
2. Click **Add patient**.
3. Enter a new patient and leave follow-up date/time blank.
4. The backend creates a follow-up task for about one minute later.
5. The automation worker checks every 15 seconds.
6. With no Azure Communication Services credentials, the outreach is marked `SIMULATED` but is stored exactly like a real provider event.
7. Open the patient record to see the conversation/task activity.

For patient chat:

1. Sign in as `john / patient123`.
2. Open **Care chat**.
3. Try:
   - `Do I still need treatment?`
   - `Help me book an appointment`
   - `I have severe swelling and pain`
   - `How much will it cost?`
4. Booking displays selectable slots. Symptoms create a clinical escalation. Fees create a financial escalation.

## Demo data vs real data

There is no separate demo engine. Seeded patients have `source=DEMO`. Patients entered through the UI have `source=REAL`; self-created patient profiles use `source=SELF_REGISTERED`. All of them use the same tables, agent APIs, follow-up tasks, conversations, appointments and escalations.

## Account creation

### Patient

A patient can register from the login screen. A patient profile is created automatically. If the supplied email/phone matches an existing clinic patient record, the account links to that record so the user sees their existing care data.

For a production healthcare deployment, add verified identity/OTP before allowing automatic linking by email or phone.

### Doctor / Staff

Doctor and staff registration requires the value of `CLINIC_ACCESS_CODE`. Change the default before deployment and store it as an Azure Container Apps secret/Key Vault secret.

## Automation behavior

```text
Patient record created/updated
        ↓
Follow-up task scheduled
        ↓
Background worker detects due task
        ↓
SMS / Voice provider adapter
        ↓
Conversation event stored
        ↓
Patient reply enters agent
        ↓
Intent + context processing
        ↓
Book appointment / answer safely / escalate to clinic
        ↓
Live dashboard update
```

## Azure modes

The local app works without Azure credentials.

- **Azure OpenAI unset:** clinic-approved deterministic response templates are used.
- **Azure OpenAI set:** eligible treatment/general replies can use Azure OpenAI for context-aware wording.
- **Azure Communication Services unset:** SMS/voice events are simulated and logged.
- **Azure Communication Services + phone number set:** the communication adapter can send through the configured Azure resource.
- **SQLite locally:** easy demo development.
- **Azure PostgreSQL:** set `DATABASE_URL=postgresql+asyncpg://...` for persistent cloud data.

## Docker production build

The root Dockerfile compiles React and serves it from FastAPI as one container:

```powershell
docker build -t saidatta-careflow:v3 .
docker run --rm -p 8000:8000 --env-file .env saidatta-careflow:v3
```

Then open `http://localhost:8000`.

## Azure deployment

See `azure/README-AZURE.md` and `azure/deploy-azure.ps1`.

From the project root after `az login` and selecting your subscription:

```powershell
.\azure\deploy-azure.ps1
```

The script provisions the core resources and builds the single production image in Azure Container Registry. Azure OpenAI model/version availability varies by subscription and region, so change the deployment parameters to a model/version available to your Azure account.

## Important production items

This is a working demo/real-data application pattern, but before use with actual patient health information you should add your organization's required identity verification, consent, audit/retention controls, private networking, provider-specific compliance configuration, backups, monitoring, and clinical governance. Never use demo passwords or the default clinic access code in production.
