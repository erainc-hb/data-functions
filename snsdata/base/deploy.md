

```
gcloud functions deploy spova-dp-sportspro-raw-function --entry-point=main --region=us-central1 --runtime=python38 --timeout=540 --memory=4GB --allow-unauthenticated --trigger-topic=spova-dp-sportspro-raw-topic
```