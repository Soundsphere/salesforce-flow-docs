# ContractAfterUpdate - Create Followup Contract Renewal

## 1. Flow identity

| Field | Value |
|---|---|
| Flow label | ContractAfterUpdate - Create Followup Contract Renewal |
| API name | ContractAfterUpdate_CreateFollowupContractRenewal |
| Type | Record-triggered Flow |
| Status | Active |
| Active version | Missing / requires validation |
| API version | 66.0 |
| Object / process area | Contract |
| Trigger / timing | After-save record-triggered Flow on Contract; configured for create and update when `StatusCode = Activated`; includes scheduled paths |
| Source metadata | `force-app/main/default/flows/ContractAfterUpdate_CreateFollowupContractRenewal.flow-meta.xml` |
| Owner | Missing / requires validation |
| Documentation status | Draft generated from evidence |

## 2. Business purpose

- Confirmed from evidence: This Flow runs on Contract records with `StatusCode = Activated`, creates a Task related to the Contract, updates Account status when the related Account is still marked as `Prospect`, and contains an update to set `Contract.Renewal_Status__c` to `Scheduled`.
- Inferred from technical structure: The automation appears to support contract activation and renewal follow-up by creating future work before the Contract end date and by moving the related Account from prospect to customer.
- Proposed interpretation: The likely business purpose is to ensure activated contracts are prepared for renewal follow-up and that Account lifecycle status reflects an active customer relationship.
- Requires validation: Confirm the intended business owner, whether the Flow should run on both create and update, whether it should run only when status changes to Activated, and whether the renewal status update is currently reachable in the Flow path.

## 3. Trigger and scope

Confirmed from evidence:

- Object: `Contract`.
- Trigger type: `RecordAfterSave`.
- Record trigger type: `CreateAndUpdate`.
- Entry criterion: `StatusCode EqualTo Activated`.
- Filter logic: `and`.
- The Flow is active and built with Lightning Flow Builder.

Scheduled behaviour confirmed from evidence:

- An unnamed scheduled path uses `AsyncAfterCommit` and connects to `ChangeAccountStatus`.
- A scheduled path named `90 Days Before End Date` / `X90_DaysBeforeEndDate` runs `-90` days from the Contract `EndDate` and connects to `CreateRenewalTask`.

Missing / requires validation:

- The evidence does not show a prior-value condition such as "Status changed from another value to Activated." The Flow name and description imply after-update behaviour, but the extracted trigger configuration is create and update with `StatusCode = Activated`.
- The evidence does not show whether records without an `EndDate` are prevented from entering the scheduled path.
- The evidence does not show whether recursion, duplicate Task creation, or repeated update handling is controlled elsewhere.

## 4. Main logic

Confirmed from evidence:

- When a Contract meets the entry criterion `StatusCode = Activated`, the Flow has an async after-commit path that updates the related Account if the Account's `Status__c` is `Prospect`.
- That Account update changes `Status__c` to `Customer`.
- The Flow has a scheduled path 90 days before `Contract.EndDate`.
- The scheduled path creates a Task with:
  - `OwnerId = $Record.Account.OwnerId`
  - `Status = Not Started`
  - `Subject = Create Renewal Contract`
  - `WhatId = $Record.Id`
- The Flow contains an update element that sets `Renewal_Status__c = Scheduled` on the triggering Contract.

Inferred from technical structure:

- The Task is intended to create follow-up work for the Account owner before the Contract reaches its end date.
- The Account status update is intended to reflect that an Account associated with an activated Contract should no longer remain in a prospect lifecycle state.

Missing / requires validation:

- The connector graph in the evidence shows `X90_DaysBeforeEndDate -> CreateRenewalTask` and the unnamed scheduled path to `ChangeAccountStatus`; it does not show a connector to `UpdateRenewalStatus`. Validate whether `UpdateRenewalStatus` is reachable in the actual Flow canvas.

## 5. Key decisions

| Decision | Evidence | Interpreted meaning | Notes |
|---|---|---|---|
| Contract activation criterion | Start condition: `StatusCode EqualTo Activated` | Confirmed from evidence: the Flow is scoped to activated Contracts. | Validate whether this should mean "is Activated" or "changed to Activated." |
| Account status eligibility | `ChangeAccountStatus` condition: `Status__c EqualTo Prospect` | Inferred from technical structure: only prospect Accounts are promoted to customer status by this Flow. | Confirm whether other statuses should remain unchanged. |
| Renewal follow-up timing | Scheduled path offset: `-90 Days` from `EndDate` | Confirmed from evidence: renewal Task creation is scheduled 90 days before Contract end date. | Validate handling for missing or changed `EndDate`. |
| Task ownership | `OwnerId = $Record.Account.OwnerId` | Inferred from technical structure: renewal follow-up is assigned to the related Account owner. | Validate whether Contract owner, Account owner, or queue ownership is the intended assignment rule. |

## 6. Data changes and side effects

### Direct effects

| Operation | Object | Field / target | Value / source | Notes |
|---|---|---|---|---|
| Create record | Task | `OwnerId` | `$Record.Account.OwnerId` | Confirmed from evidence. Creates owner-assigned follow-up work. |
| Create record | Task | `Status` | `Not Started` | Confirmed from evidence. |
| Create record | Task | `Subject` | `Create Renewal Contract` | Confirmed from evidence. |
| Create record | Task | `WhatId` | `$Record.Id` | Confirmed from evidence. Relates the Task to the triggering Contract. |
| Update record | Account | `Status__c` | `Customer` | Confirmed from evidence. Applies when related Account `Status__c = Prospect`. |
| Update record | Contract | `Renewal_Status__c` | `Scheduled` | Confirmed as an element in evidence; reachability requires validation. |

### Side effects

Confirmed from evidence:

- A Task may be created for renewal follow-up.
- The related Account's custom `Status__c` field may be changed from `Prospect` to `Customer`.
- No Apex actions, subflows, email alerts, notifications, platform events, external actions, formulas, variables, constants, choices, or text templates were found in the extracted evidence.

### Potential downstream effects

- Inferred from technical structure: Creating a Task may trigger Task automation, assignment notifications, reporting changes, activity timelines, or user work queues outside the provided evidence.
- Inferred from technical structure: Updating Account `Status__c` may trigger Account automation, validation rules, integrations, reports, or lifecycle processes outside the provided evidence.
- Inferred from technical structure: Updating Contract `Renewal_Status__c`, if reachable, may affect renewal reporting or downstream Contract automation.
- Missing / requires validation: Related Contract, Account, and Task automations were not included in the provided evidence, so downstream behaviour cannot be fully confirmed.

## 7. Dependencies

### Data dependencies

- `Contract`
- `Contract.StatusCode`
- `Contract.EndDate`
- `Contract.Renewal_Status__c`
- `$Record.Id`
- `$Record.Account`
- `$Record.Account.OwnerId`
- `Account.Status__c`
- `Task.OwnerId`
- `Task.Status`
- `Task.Subject`
- `Task.WhatId`

### Automation dependencies

- Missing / requires validation: Other Contract, Account, or Task automation may run because this Flow creates a Task and updates Account and potentially Contract fields.

### Integration / action dependencies

- Confirmed from evidence: No action call side effects were found.
- Missing / requires validation: The provided evidence does not confirm whether downstream integrations respond to Task, Account, or Contract changes.

### Configuration dependencies

- The Flow depends on Contract status values including `Activated`.
- The Flow depends on Account `Status__c` values including `Prospect` and `Customer`.
- The scheduled renewal Task depends on `Contract.EndDate`.
- The Task owner assignment depends on the related Account owner being populated and valid for Task ownership.

### Unknown / requires validation

- Whether `UpdateRenewalStatus` is connected and executes.
- Whether duplicate Task creation is prevented on repeated Contract updates.
- Whether Contract records created directly in Activated status should enter this automation.
- Whether scheduled paths are rescheduled or cancelled when `EndDate` or `StatusCode` changes after initial scheduling.

## 8. Error handling and observability

Confirmed from evidence:

- No explicit fault connectors were found.
- No custom logging, alerting, or error notification actions were found in the extracted evidence.

Inferred from technical structure:

- Failures in Task creation or Account/Contract updates would rely on standard Flow transaction behaviour and Salesforce error surfacing unless additional platform-level monitoring exists outside this evidence.

Missing / requires validation:

- Confirm how admins monitor failed scheduled path interviews.
- Confirm whether validation rules, required fields, owner constraints, or Task automation can cause failures.
- Confirm whether business users receive any visible error or notification if follow-up Task creation fails.

## 9. Testing and validation

Proposed validation scenarios:

- Create or update a Contract so `StatusCode = Activated` and verify the Flow enters the expected paths.
- Validate whether the Flow runs when a Contract is created already Activated.
- Validate whether the Flow runs repeatedly when an already Activated Contract is edited.
- Validate whether an Account with `Status__c = Prospect` is changed to `Customer`.
- Validate that Accounts with other `Status__c` values are not changed unexpectedly.
- Validate that a Task is created 90 days before `Contract.EndDate`.
- Validate Task field values: owner, status, subject, and related Contract.
- Validate behaviour when the Contract has no `EndDate`, when `EndDate` changes, or when `EndDate` is within 90 days.
- Validate whether `Contract.Renewal_Status__c` is set to `Scheduled` in actual execution.
- Review related Account, Contract, and Task automation for downstream effects.

## 10. Change notes

- Confirmed from evidence: No change notes were found in the XML metadata.
- Missing / requires validation: No release ticket, deployment context, stakeholder request, or business change rationale was provided with the evidence file.

## 11. Open questions for human validation

- Who owns this Flow from a business and administrative perspective?
- Should the Flow run on both Contract create and update, or only when an existing Contract changes to Activated?
- Should the Flow create only one renewal Task per Contract?
- What should happen if `Contract.EndDate` is blank, changed, or already less than 90 days away?
- Is the Account owner always the correct renewal Task owner?
- Should changing Account `Status__c` from `Prospect` to `Customer` happen for every activated Contract?
- Is `UpdateRenewalStatus` intentionally disconnected, or is the connector missing from the extraction?
- What downstream automations, reports, integrations, or notifications depend on Task creation, Account status changes, or Contract renewal status changes?
- What monitoring process exists for scheduled path failures or failed record updates?

## Map row candidate

| Name | Type | Object / Process Area | Trigger / Timing | Purpose | Data Changed | Side Effects / Dependencies | Risk / Criticality | Owner | Documentation Status | Last Reviewed | Detail Link |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ContractAfterUpdate - Create Followup Contract Renewal | Record-triggered Flow | Contract | After-save; create and update; `StatusCode = Activated`; scheduled path 90 days before `EndDate` | Proposed: schedule renewal follow-up and update customer lifecycle status when a Contract becomes active | Creates Task; updates `Account.Status__c`; contains Contract `Renewal_Status__c` update requiring reachability validation | Task creation, Account lifecycle update, possible Contract renewal tracking; downstream Contract/Account/Task automation not visible in evidence | Proposed: Medium; requires validation because it creates work and changes Account status | Missing / validate | Draft generated from evidence | 2026-05-07 | `docs/automation/living-technical-blueprint.md` |

## Review notes

### Confirmed from evidence

- The source evidence file documents one active Salesforce Flow.
- The Flow is an after-save record-triggered Flow on `Contract`.
- The Flow is configured for create and update with entry criterion `StatusCode = Activated`.
- The Flow creates a `Task` scheduled 90 days before `Contract.EndDate`.
- The Flow updates the related Account `Status__c` to `Customer` when it is currently `Prospect`.
- The evidence contains a Contract update element that sets `Renewal_Status__c` to `Scheduled`.
- No explicit fault connectors were found.

### Inferred / proposed

- The Flow appears to support renewal follow-up for activated Contracts.
- The renewal Task appears intended for the related Account owner.
- The Account status update appears intended to move prospect Accounts into customer status after Contract activation.
- Proposed risk is medium because the Flow creates user work and changes Account lifecycle data, but this risk level is not explicitly present in the evidence.

### Missing or requires validation

- Business owner and administrative owner.
- Whether "activated" means current status only or status changed to Activated.
- Whether `UpdateRenewalStatus` is reachable in the actual Flow.
- Duplicate prevention for renewal Tasks.
- Downstream effects from Account, Contract, and Task automation.
- Failure monitoring for scheduled path interviews and record updates.

### Possible documentation risks

- The Flow name suggests after-update behaviour, but the metadata says create and update.
- The generated description says "status changes to Activated," but the extracted criterion only confirms `StatusCode = Activated`.
- Treating the Contract renewal status update as definitely executed may be unsafe until the Flow path is validated.
- The evidence file is a metadata extraction only; business purpose, ownership, and operational criticality require human validation.
