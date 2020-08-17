---
layout: default
nav_order: 0
---
# Description

This service receives records from a given Kafka topic, downloads the items
from the S3 server and applies Insights rules to downloaded tarball.

JSON containing Insights rules results is sent to a different Kafka topic
and logged in a way to be determined.

Incoming and outgoing Kafka topics are configurable, these can be even handled
by different Kafka instances.

### Integration with other services

Please look at [CCX Docs/Customer
Services](https://ccx-docs.cloud.paas.psi.redhat.com//customer/index.html) with
an explanation how the CCX Data Pipeline is connected with other services.
