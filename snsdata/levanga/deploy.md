

```
gcloud functions deploy snsdata-levanga-function --entry-point=main --region=us-central1 --runtime=python38 --timeout=540 --memory=4GB --env-vars-file=env.yaml --allow-unauthenticated --trigger-topic=snsdata-levanga-topic
```