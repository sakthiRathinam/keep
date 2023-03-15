---
sidebar_label: Multistep Alert Example
sidebar_position: 7
---

#  Multistep Alert Example

```bash
# Check both databases prod1 and prod2 and alert if any of them has less than 10% disk space left.
alert:
  id: db-disk-space
  description: Check that the DB has enough disk space
  steps:
    - name: db-prod1-no-space
      provider:
        type: mock
        config: "{{ providers.db-server-mock }}"
        with:
          command: df -h | grep /dev/disk3s1s1 | awk '{ print $5}' # Check the disk space
          command_output: 91% # Mock
      condition:
        - type: threshold
          value:  "{{ steps.this.results }}"
          compare_to: 90% # Trigger if more than 90% full
          alias: A
    - name: db-prod2-no-space
      provider:
        type: mock
        config: "{{ providers.db-server-mock }}"
        with:
          command: df -h | grep /dev/disk3s1s1 | awk '{ print $5}' # Check the disk space
          command_output: 94.5% # Mock
      condition:
        - type: threshold
          value:  "{{ steps.this.results }}"
          compare_to: 90% # Trigger if more than 90% full
          alias: B
  actions:
    - name: trigger-telegram
      # trigger the action only if both conditions are met:
      if: "{{ A }} or {{ B }}"
      provider:
        type: telegram
        config:
          authentication:
            bot_token:  "{{ env.TELEGRAM_BOT_TOKEN }}"
        with:
          chat_id: "{{ env.TELEGRAM_CHAT_ID }}"
          message: Keep Alert Test

providers:
  db-server-mock:
    description: Paper DB Server
    authentication:

```

# Breakdown

## Steps
In this example we can see two steps:
- db-prod1-no-space - checks db space of db prod1
- db-prod2-no-space - checkd db space of db prod2

### Conditions
Each of the steps has the same threshold condition:
```
condition:
    - type: threshold
      value:  "{{ steps.this.results }}"
      compare_to: 90% # Trigger if more than 90% full
```
But now we've added an `alias` to each condition, so it'll be easier to check it in the `action` itself.

The condition result can also be accessed through `{{ step.step-id.conditions[i].result }}`.

## Action (if statement)
Now, the action now use the `if` statement to alert if one of the databases has less than 10% disk space left.

We could use `if: "{{ A }} and {{ B }}"` to alert only if both databases has less than 10% disk space left. Note that its the default behavior so you may achieve the same without specifying `if` statement.
