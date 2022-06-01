

```
gcloud functions deploy snsdata-northern-happinets-function --entry-point=main --region=us-central1 --runtime=python38 --timeout=540 --memory=4GB --env-vars-file=env.yaml --allow-unauthenticated --trigger-topic=snsdata-northern-happinets-topic
```