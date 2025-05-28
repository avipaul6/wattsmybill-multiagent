#!/bin/bash
# deploy.sh - Deploy to Cloud Run

PROJECT_ID="wattsmybill-dev"
SERVICE_NAME="energy-plans-etl"
REGION="australia-southeast1"  # Sydney region

echo "🚀 Deploying Energy Plans ETL to Cloud Run..."

# Build and deploy
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 1 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

echo "✅ Deployment complete!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"

# Test the health endpoint
echo "🧪 Testing health endpoint..."
curl -s "$SERVICE_URL/health" | jq .

echo ""
echo "📋 Available endpoints:"
echo "  GET  $SERVICE_URL/health"
echo "  GET  $SERVICE_URL/stats" 
echo "  POST $SERVICE_URL/extract-plans"
echo "  POST $SERVICE_URL/extract-tariffs"
echo "  POST $SERVICE_URL/full-etl"