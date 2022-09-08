# Configuration

The `config.yaml` is an standard **Insights Core Messaging** configuration file.
To learn about its structure and configuring some common things, you probably
want to read its documentation:

[Insights Core Messaging
documentation](https://github.com/RedHatInsights/insights-core-messaging#example-configuration).

Some of the specific **ccx-data-pipeline** configuration points are in the
`service` section, where the specific _consumer_, _downloader_ and _publisher_
are configured.

- `consumer` name refers to the class `ccx_data_pipeline.consumer.Consumer`. The
  arguments passed to the initializer are defined in the `kwargs` dictionary
  initializer. The most relevants are:
  - `incoming_topic`: the Kafka topic to subscribe the consumer object.
  - `group_id`: Kafka group identifier. Several instances of the same pipeline
    will need to be into the same group in order to not process the same
    messages.
  - `bootstrap_servers`: a list of "IP:PORT" strings where the Kafka server is
    listening.
  - `max_record_age`: an integer that defines the amount of seconds for ignoring
    older Kafka records. If a received record is older than this amount of
    seconds, it will be ignored. By default, messages older than 2 hours will be
    ignored. To disable this functionality and process every record ignoring its
    age, use `-1`.
- `downloader`: name refers to the class
  `ccx_data_pipeline.http_downloader.HTTPDownloader`. The only argument that can
  be passed to the initializer is:
  - `max_archive_size`: this is an optional argument. It will specify the
    maximum size of the archives that can be processed by the pipeline. If the
    downloaded archive is bigger, it will be discarded. The parameter should be
    an string in a human-readable format (it accepts units like KB, KiB, GB,
    GiB...
- `publisher` name refers to the class `ccx_data_pipeline.publisher.Publisher`
  and it also allow to define the arguments passed to the initializer modifying
  the `kwargs` dictionary:
  - `outgoing_topic`: a string indicating the topic where the reported results
    should be sent.
  - `bootstrap_servers`: same as in `consumer`, a list of Kafka servers to
    connect
- `watchers`: it has a list of `Watcher` objects that will receive notifications
  of events during the
  pipeline processing steps. The default configured one is
  `ccx_data_pipeline.consumer_watcher.ConsumerWatcher` that serve some
  statistics for [Prometheus service](https://prometheus.io/). The port where
  the `prometheus_client` library will listen for petitions is configurable
  using `kwargs` dictionary in the same way as `consumer` and `publisher`. The
  only recognized option is:
  - `prometheus_port`: an integer indicating the port where the
    `prometheus_client` will listen for server petitions. If not present,
    defaults to 8000.

## Environment variables

In addition to the configuration mentioned above, some other behaviours can be
configured through the definition of environment variables.

All the YAML file is parsed by the Insights Core Messaging library, that
includes support for using environment variables with default values as values
for any variable in the configuration file.

As an example, given an environment variable named `CDP_INCOMING_TOPIC` that
contains the Kafka topic name where the consumer should read, you can put
`${CDP_INCOMING_TOPIC}` as the value for the `consumer`/`incoming_topic`
configuration.

Following the same example, if you want that a default value is used in case of
`CDP_INCOMING_TOPIC` is not defined, you can specify
`${CDP_INCOMING_TOPIC:default_value}`. In this case, the environment variable
will take precedence over the default value, but this default will be used in
case the environment variable is not defined.

In addition to the YAML configuration, another important note about the needed
environment variables:

### Cloud Watch configuration

To enable the sending of log messages to a Cloud Watch instance, you should
define **all** the following environment variables:

- `CW_AWS_ACCESS_KEY_ID`: The AWS access key for creating the Cloud Watch
  session.
- `CW_AWS_SECRET_ACCESS_KEY`: The AWS secret access key for creating the Cloud
  Watch session.
- `AWS_REGION_NAME:`: An AWS region name where the Cloud Watch authentication
  should be done.
- `CW_LOG_GROUP`: The logging group that will be used by `ccx-data-pipeline` to
  publish its messages.
- `CW_STREAM_NAME`: A name to distinguish this application logs inside the log
  group.

If any of these environment variables are not defined, the Cloud Watch service
cannot be configured and won't be used at all.
