---
layout: page
nav_order: 2
---
# Implementation

## Data consumer

Every time a new record is sent by Kafka to the subscribed topic, the
`ccx_data_pipeline.consumer.Consumer` will handle and process it, storing the
needed information from the record and returning the URL to the archive in the
corresponding S3 bucket.

### Format of the received Kafka records

```json5
{
  "account": 123456, // (uint)
  "principal": 9, // (uint)
  "size": 55099, // (uint)
  "url": "https://insights-dev-upload-perm.s3.amazonaws.com/e927438c126040dab7891608447da0b5?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJW4PUHKGSOIEEI7A%2F20200123%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20200123T161559Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=3e123beac8503f4338f611f85b053f7f15e69e2748228f9f98b6986e7c06fb6c", // (string)
  "b64_identity": "eyJlbnRpdGxlbWVudHMiOnsiaW5zaWdodHMiOnsiaXNfZW50aXRsZWQiOnRydWV9LCJjb3N0X21hbmFnZW1lbnQiOnsiaXNfZW50aXRsZWQiOnRydWV9LCJhbnNpYmxlIjp7ImlzX2VudGl0bGVkIjp0cnVlfSwib3BlbnNoaWZ0Ijp7ImlzX2VudGl0bGVkIjp0cnVlfSwic21hcnRfbWFuYWdlbWVudCI6eyJpc19lbnRpdGxlZCI6dHJ1ZX0sIm1pZ3JhdGlvbnMiOnsiaXNfZW50aXRsZWQiOnRydWV9fSwiaWRlbnRpdHkiOnsiaW50ZXJuYWwiOnsiYXV0aF90aW1lIjoxNDAwLCJvcmdfaWQiOiIxMjM4MzAzMiJ9LCJhY2NvdW50X251bWJlciI6IjYyMTIzNzciLCJhdXRoX3R5cGUiOiJiYXNpYy1hdXRoIiwidXNlciI6eyJmaXJzdF9uYW1lIjoiSW5zaWdodHMiLCJpc19hY3RpdmUiOnRydWUsImlzX2ludGVybmFsIjpmYWxzZSwibGFzdF9uYW1lIjoiUUUiLCJsb2NhbGUiOiJlbl9VUyIsImlzX29yZ19hZG1pbiI6dHJ1ZSwidXNlcm5hbWUiOiJpbnNpZ2h0cy1xZSIsImVtYWlsIjoiam5lZWRsZStxYUByZWRoYXQuY29tIn0sInR5cGUiOiJVc2VyIn19", // (string)
  "timestamp": "2020-01-23T16:15:59.478901889Z" // (string)
}
```

The attribute `b64_identity` contains another JSON encoded by BASE64 encoding.
User and org identities are stored here:

```json5
    "identity": {
        "account_number": "6212377",
        "auth_type": "basic-auth",
        "internal": {
            "auth_time": 1400,
            "org_id": "12383032"
        },
        "type": "User",
        "user": {
            "email": "jneedle+qa@redhat.com",
            "first_name": "Insights",
            "is_active": true,
            "is_internal": false,
            "is_org_admin": true,
            "last_name": "QE",
            "locale": "en_US",
            "username": "insights-qe"
        }
```

## Download

The `ccx_data_pipeline.http_downloader.HTTPDownloader` class is provided to get
the archive from a HTTP URL, normally obtained by the class described above.
This downloader simply gets the archive from the URL, but it performs some
checks, like the URL matching several regular expressions to avoid getting
archives from unknown servers, or checking the size of the archive.

## Processing

As this service is built on top of
[`insights-core-messaging`](https://github.com/RedHatInsights/insights-core-messaging),
the processing of the downloaded archives is done by the default engine provided
by the framework.

The ICM `Engine` class takes the downloaded archive and, using the configured
rules, processes it and generates a JSON report. This report is handled and
published using the configured _publisher_.

## Reporting

This service provides a _publisher_ class that can send the generated reports to
a Kafka topic. This class is `ccx_data_pipeline.kafka_publisher.KafkaPublisher`.
The report generated by the framework will be enhanced with more context
information taken from different sources, like the organization ID or the "last
checked" timestamp (taken from the incoming Kafka record containing the URL to
the archive).

The generated JSON has the following format:

```json5
{
  "OrgID": 123456, // (int) - number that we get from b64_identity field
  "ClusterName": "aaaaaaaa-bbbb-cccc-dddd-000000000000", // (string) - cluster UUID  that we read from URL
  "Report": "{...}", // (string) - stringified JSON, that contains results of executing rules,
  "LastChecked": "2020-01-23T16:15:59.478901889Z" // (string) - time of the archive uploading in ISO 8601 format, gotten from "timestamp" field
}
```

The fields come from:

- `OrgID`: retrieved from the incoming JSON, codified inside the `b64_identity`
  value. It is extracted from `identity-internal-org_id` path of keys.
- `ClusterName`: the cluster name is retrieved from the downloaded archive. When
  the download successes and the archive is extracted prior to its processing by
  the engine, the cluster ID is read from a file named `config/id`.
- `Report`: is the JSON generated by the engine when the archive is processed.
- `LastChecked`: this field is copied directly from the incoming Kafka record,
  as `timestamp` key.

## Cluster name extraction internals

As the cluster ID is only present inside the archive and the set of rules to be
executed is configurable, this pipeline cannot relay on the executed rules to
get the cluster name.

For that reason, a mixed `Watcher` was created: `ClusterIdWatcher`, that
inherits from both `EngineWatcher` and `ConsumerWatcher`. This double
inheritance allows this watcher to receive notification from both entities of
the pipeline. The relevant events for this watcher are:

- `on_recv`: a consumer event used to store the `ConsumerRecord` object, needed
  to store the cluster name, when extracted
- `on_extract`: an engine event triggered when the archive is extracted, but not
  already processed. At this point, the files on the archive are available in
  the internal storage, so the relevant file can be read in order to store its
  content as cluster name.