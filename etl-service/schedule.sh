#!/bin/bash
# schedule.sh - Set up Cloud Scheduler jobs

PROJECT_ID="wattsmybill-dev"
SERVICE_NAME="energy-plans-etl"
REGION="australia-southeast1"

# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Could not find Cloud Run service URL. Deploy first with ./deploy.sh"
    exit 1
fi

echo "🕐 Setting up Cloud Scheduler jobs..."

# Job 1: Weekly full plans extraction (Sundays at 2 AM AEST)
gcloud scheduler jobs create http weekly-plans-extraction \
    --location $REGION \
    --schedule "0 2 * * 0" \
    --time-zone "Australia/Sydney" \
    --uri "$SERVICE_URL/extract-plans" \
    --http-method POST \
    --headers "Content-Type=application/json" \
    --message-body '{}' \
    --attempt-deadline 3600s \
    --max-retry-attempts 2 \
    --description "Weekly extraction of energy plans"

# Job 2: Daily tariff updates for major retailers (Mon-Fri at 3 AM AEST) 
gcloud scheduler jobs create http daily-tariff-updates \
    --location $REGION \
    --schedule "0 3 * * 1-5" \
    --time-zone "Australia/Sydney" \
    --uri "$SERVICE_URL/extract-tariffs" \
    --http-method POST \
    --headers "Content-Type=application/json" \
    --message-body '{"sample_size": 200}' \
    --attempt-deadline 3600s \
    --max-retry-attempts 2 \
    --description "Daily tariff updates for sample plans"

# Job 3: Monthly full ETL (1st of each month at 1 AM AEST)
gcloud scheduler jobs create http monthly-full-etl \
    --location $REGION \
    --schedule "0 1 1 * *" \
    --time-zone "Australia/Sydney" \
    --uri "$SERVICE_URL/full-etl" \
    --http-method POST \
    --headers "Content-Type=application/json" \
    --message-body '{}' \
    --attempt-deadline 3600s \
    --max-retry-attempts 1 \
    --description "Monthly full ETL process"

echo "✅ Scheduler jobs created!"
echo ""
echo "📅 Scheduled jobs:"
echo "  • Weekly plans extraction: Sundays 2 AM AEST"
echo "  • Daily tariff updates: Mon-Fri 3 AM AEST"  
echo "  • Monthly full ETL: 1st of month 1 AM AEST"
echo ""
echo "🔧 Manage jobs at: https://console.cloud.google.com/cloudscheduler"

# List the created jobs
gcloud scheduler jobs list --location $REGION