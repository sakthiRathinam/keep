---
sidebar_label: Opsgenie Provider
---

# OpsGenie Provider

:::note Brief Description
OpsGenie Provider is a provider that allows to create alerts in OpsGenie.
:::

## Inputs
The `notify` function in the `OpsgenieProvider` use OpsGenie [CreateAlertPayload](https://github.com/opsgenie/opsgenie-python-sdk/blob/master/docs/CreateAlertPayload.md):

### Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**user** | **str** | Display name of the request owner | [optional]
**note** | **str** | Additional note that will be added while creating the alert | [optional]
**source** | **str** | Source field of the alert. Default value is IP address of the incoming request | [optional]
**message** | **str** | Message of the alert |
**alias** | **str** | Client-defined identifier of the alert, that is also the key element of alert deduplication. | [optional]
**description** | **str** | Description field of the alert that is generally used to provide a detailed information about the alert. | [optional]
**responders** | **list**[[Recipient](https://github.com/opsgenie/opsgenie-python-sdk/blob/master/docs/Recipient.md)] | Responders that the alert will be routed to send notifications | [optional]
**visible_to** |  **list**[[Recipient](https://github.com/opsgenie/opsgenie-python-sdk/blob/master/docs/Recipient.md)] | Teams and users that the alert will become visible to without sending any notification | [optional]
**actions** | **list[str]** | Custom actions that will be available for the alert | [optional]
**tags** | **list[str]** | Tags of the alert | [optional]
**details** | **dict(str, str)** | Map of key-value pairs to use as custom properties of the alert | [optional]
**entity** | **str** | Entity field of the alert that is generally used to specify which domain alert is related to | [optional]
**priority** | **str** | Priority level of the alert | [optional]


## Authentication Parameters
The OpsgenieProviderAuthConfig class takes the following parameters:
```python
api_key (str | None): API key, which is a user or team API key. Optional, default is `None`. *Required*
```

## Connecting with the Provider

To use the Opsgenie Provider, you'll need to provide api_key.

You can create an integration key under Settings -> Integrations -> Add API
Note: if you are in the free tier, the integration key can be created under Teams -> Your team -> Integrations -> Add Integration (API)

## Useful Links
- How to create Opsgenie API Integration - https://support.atlassian.com/opsgenie/docs/create-a-default-api-integration/
- How to get Opsgenie Integration Api Key - https://community.atlassian.com/t5/Opsgenie-questions/OpsGenie-API-Create-alert-Authentication-problem/qaq-p/1531047?utm_source=atlcomm&utm_medium=email&utm_campaign=immediate_general_question&utm_content=topic#U1531256
