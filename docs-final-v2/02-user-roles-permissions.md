# 02 — User Roles & Permissions

Status: DRAFT V2 — authorization source after approval

## Authorization boundary

Every protected request requires backend authentication, Company/Tenant membership, enabled-module permission, role/action permission, Branch scope where relevant, and object/field ownership checks. A Company, Branch, Investor, Vehicle, Job or image UUID grants no access by itself. Default deny applies to every new module and operation; frontend visibility is only presentation. A Platform operator's access to one Company never implies access to another Company's business data.

Company-wide views aggregate only the user's explicitly authorized Company scope and permitted Branch records. Same-Company previous-Branch history may be read by authorized users; another Branch's original operational record is normally read-only unless Company-level correction authority is explicitly granted. Phase 6 Garage mutation across Branches is default-deny and adds no such correction grant. Company and Branch access checks apply to reports, exports, search, files, jobs, notifications and audit as well as ordinary APIs.

## Existing business roles

| Role | Current authority | Boundary |
|---|---|---|
| Owner | Read, monitor, filter, analyse and audit authorized Company-wide business information, including authorized Branch views and Owner AI | No ordinary operational, finance, percentage, payout, correction or closure mutation |
| Accountant / Operations Admin | Primary authorized business-operation writer: Investors/Fund, Stock Vehicles, approved Expenses, Sales, actual Buyer receipts/refunds, Profit and interim payment confirmations, reconciliations, corrections, Labour, Garage/Accounting entries, media and settlement where a rule grants the action | Company, Branch, module, object and current-position checks; no automatic Platform control authority |
| Investor | View own permitted Fund, Stock Vehicles, Profit, interim/reconciliation, recoverable and exit/settlement positions; submit normal Exit request | No authoritative finance write or access to another Investor's private data; other Vehicles only via approved public view |
| Media User | Manage authorized Vehicle images, approved public fields, display price/information, publication and public availability | No internal finance, Investor private data, core Vehicle lifecycle or Garage accounting mutation |
| Platform Back Office Admin | Manage Companies, Branch administration, Tenant activation/suspension, accounts/membership, module enablement/configuration, protected Investor agreements and business rates, Owner distribution percentages, sensitive Company defaults, future plan/subscription settings and platform audit/support; controlled Company/Tenant consolidation | Platform administration alone grants no routine Tenant financial posting or confirmation authority; financial read requires authorized scope |
| Labour | No login in current scope | Managed operational record only |

Public consumers have only the dedicated published/eligible public-safe Vehicle projection. Tenant administrator/account management is a Platform Back Office capability in the baseline; any separately empowered Company administrator requires an explicit grant, not an implied new role.

## Operational confirmation and protected configuration

- Accountant/Operations is the ordinary confirmer of actual Buyer Payments/refunds, eligible Profit Payments, Monthly Interim Payouts, recoveries, Running Capital and Company accounting transactions, Owner distributions and settlement actions only within explicitly granted Company/Branch/module/resource scope. A suggested amount, reminder or UI control never constitutes confirmation.
- Platform Back Office is the sole administrator of protected financial configuration: Investor-specific positive-share agreements, protected monthly interim rates, Owner distribution percentages, sensitive Company financial defaults and other explicitly protected business rates. A change requires specific backend protected-action permission, effective/versioned configuration and audit of old/new value, effective cycle or time, Investor/Company scope, actor and reason. Accountant/Operations uses approved effective values for ordinary authorized operations but cannot independently change protected percentages or rates. Owner has authorized visibility/notification but no mutation authority. Configuration authority is separate from ordinary transaction confirmation authority.
- Manual Loss impact, Company-level correction of another Branch record, sensitive override, and Company distributable-Profit confirmation require explicit action-level authority and reason/history. Owner read visibility does not itself grant approval or posting permission.
- Media and Investor cannot confirm internal financial movements. Platform Back Office financial review does not turn that role into the ordinary daily Accountant. No separate secondary/protected password is required.

## Module availability

An enabled module still requires the user's normal Company, Branch, role and object permissions. When a module is OFF, ordinary new module activity is denied by the backend; authorized history/read access and minimum actions needed to resolve already-open obligations remain available under explicit permission. For Phase 6 Garage, OFF denies new Jobs, optional expansion of an existing Job and unrelated new Garage charges. Existing-obligation actions may be performed only through the authoritative module (such as Accounting) and its normal permission checks. Data is retained, and re-enabling restores ordinary supported access without recreating historical records. Module OFF cannot be used to evade an open receivable, refund, recovery, interim or settlement position.

## Accounts, Portal, public access and audit

Platform Back Office provisions and manages privileged Company/Tenant assignments; Accountant may provision Investor and Media accounts within authorized operational scope as in the approved baseline. Account and membership changes retain history. Investor can request normal Exit after Terms & Conditions acceptance but cannot self-confirm financial settlement. Public APIs expose only approved public identity, name/make/model, optimized Primary image, display price, public availability and approved description where present. Never serialize private internal entities for public, Media or Investor views.

Owner AI is read-only over the Owner's verified authorized Company/Branch scope and cannot create financial truth or mutate records. Corrections, configuration, module changes, account actions and sensitive financial confirmations retain actor, time, scope, old/new information and reason where relevant.

## Authorization decisions pending

- **BUSINESS DECISION REQUIRED:** Define broader Company-level correction and manual Loss confirmation authority, including whether the existing Accountant role may exercise it across Branches or only through a separate explicit grant. Phase 6 Garage keeps cross-Branch mutation default-deny and does not depend on that broader grant.
- **BUSINESS DECISION REQUIRED:** Define whether and when Platform Back Office support may read a Company's private financial records beyond explicit Company assignment, and the minimum OFF-module actions for modules beyond the Phase 6 Garage boundary locked in 10.

## Approved Business Decision Additions

### ADDITION — Owner remains read-only for ordinary Accounting

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Owner may read, monitor, analyse, report, and audit within authorized Company/Branch scope.
- Owner has no ordinary Accounting mutation authority, including Income, Expense, Receipt, Payment, Cash/Bank account, category, opening balance, transfer, correction, or financial finalization actions.

**Scope**
- Owner-facing Company Accounting visibility and permissions.

**Preserve unchanged**
- Existing authorized read/report/audit visibility remains. Accountant permissions and Platform protected-configuration boundaries remain separately enforced.

**Supersedes**
- None. This confirms the existing Owner read-only boundary.

**Implementation impact**
- Keep Owner actions read-only in Accounting APIs and presentation permissions.

### ADDITION — Company Accountant cross-Branch correction is Accounting-specific

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Company-level Accountant may perform authorized Accounting corrections across Branches within the same Company.
- A Branch Accountant may correct only records within their authorized Branch.
- This permission does not authorize direct overwrite or deletion of confirmed history.

**Scope**
- Accounting correction actions only, within one Company.

**Preserve unchanged**
- Company isolation, Branch attribution, BranchAssignment semantics, default-deny, linked correction history, and all non-Accounting module permissions remain unchanged.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the pending question whether the existing Accountant role may correct another Branch record, only for Company-level Accountant corrections in Accounting. Manual Loss authority, Garage/Vehicle/Investment/Sales and other-module cross-Branch actions remain unresolved or default-deny as their existing rules state.

**Implementation impact**
- Enforce the exception through an explicit Accounting action boundary; do not add a generic Company-accountant bypass.

### ADDITION — Shared Accounting categories follow Company/Branch role scope

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- The Accounting category catalogue is Company-wide and managed by the Company-level Accountant.
- Branch Accountants may use the shared catalogue but may not manage it.

**Scope**
- Company Income and Expense categories.

**Preserve unchanged**
- Company isolation, existing role identities, and historical category references remain. No Branch-, Vehicle-, or Job-specific Accounting catalogue is introduced.

**Supersedes**
- None.

**Implementation impact**
- Authorize catalogue management only for Company-level Accountant actions; filter usage by Company.

### ADDITION — Accounting OFF permits only existing-obligation actions

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- When Company Accounting is OFF, an authorized user may record a Receipt only against an Income that existed before the OFF transition, a Payment only against an Expense that existed before the transition, and audited correction/application reallocation only when needed to resolve those existing obligations.
- No new Income/Expense, account/category, opening balance, or transfer action is allowed while OFF.
- Normal role, Company, Branch, object, and audit checks still apply. Company-level Accountant scope remains within the same Company; Branch Accountant scope remains their authorized Branch.

**Scope**
- Accounting actions while the Company Accounting module is OFF.

**Preserve unchanged**
- Owner remains read-only. This is not a generic module-OFF bypass and does not grant cross-Branch access to any non-Accounting module.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the pending minimum OFF-module action question in this document, only for Accounting. Minimum actions for other modules remain unresolved.

**Implementation impact**
- Check both the pre-existing obligation and the caller's ordinary Accounting permission at the backend command boundary.

### ADDITION — Owner Accounting permission is resolved as read-only

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- In Phase 4 Accounting, Owner may read, monitor, analyse, report, and audit within authorized scope. Owner has no ordinary Accounting write or confirmation authority.
- Owner posting is resolved as unavailable for Phase 4; it is not an open business decision.

**Scope**
- Owner access to Phase 4 Accounting records and actions.

**Preserve unchanged**
- Company/Branch authorization, Accountant action scope, and Platform protected-configuration boundaries.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that Owner posting is deferred pending a later decision. This does not change future Owner Distribution governance or grant any Owner mutation permission.

**Implementation impact**
- Enforce Owner read-only at backend action policy and test every mutation as denied.

### ADDITION — Phase 4 correction Branch attribution and OFF eligibility

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Company-level Accountant may correct an Accounting record across Branches within the same Company and may set the replacement's `branch_id` to another Branch in that Company or to Company-wide (`null`) where the record type allows it.
- A Branch Accountant may correct only records in their authorized Branch. Their replacement must retain that same Branch; they cannot reassign a record to another Branch or to Company-wide. When no authorized Company-level reattribution is requested, preserve the original Branch attribution.
- While Accounting is OFF, allow a correction or application reallocation only when every affected root Accounting entry (the original event, its Income/Expense target obligation, and any linked root cash event whose application is changed) was recorded strictly before the current immutable OFF revision's `effective_from`, and only to resolve that same pre-OFF event/obligation. Equal or missing timestamps fail closed. A replacement correction row may be recorded after OFF only as an append-only child in that eligible correction chain; it must not create a new root Income/Expense obligation or attach to a post-OFF target.
- All normal role, same-Company, Branch, object, module-state, audit, and idempotency checks remain mandatory. OFF does not grant authority.

**Scope**
- Phase 4 Accounting corrections, replacement attribution, and the narrow correction/application exception while Accounting is OFF.

**Preserve unchanged**
- The cross-Branch exception remains Accounting-specific. Garage, Vehicle, Investment, Sales, and every other module keep their existing Branch rules. Company isolation and default-deny remain.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 wording that did not say whether an Accounting correction replacement may change Branch attribution; it may do so only for Company-level Accountants within the same Company. SUPERSEDES the broader OFF exception wording that checked only the cash event or obligation without requiring every affected root record and target to predate OFF.

**Implementation impact**
- Derive scope from server-side actor grants and original records; accept replacement `branch_id` only for Company-level Accountant correction actions and validate it belongs to the same Company.

### ADDITION — Accounting OFF settlement is distinct from correction eligibility

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Preserve the existing Accounting OFF settlement permission: an authorized Accountant may post a new Receipt against a pre-OFF Income or a new Payment against a pre-OFF Expense while OFF. The event, its movement, and its application are one ordinary atomic settlement; creation of that application is not correction/reallocation and is not blocked by the correction-only eligibility rule.
- A correction or application reallocation while OFF is narrower: every affected source/root event and original root target obligation must predate the current OFF revision. A linked correction replacement target may be created after OFF only as a child in that eligible correction chain; reapplication to that child is part of the same atomic correction. A standalone reallocation may target only an already-existing eligible pre-OFF obligation, never a new post-OFF root target.
- The post-OFF Receipt/Payment created by the approved settlement exception is not eligible for correction during that same OFF revision. It becomes ordinarily correctable when Accounting is enabled again, subject to the then-current policy.
- Implement the cutoff using immutable module-state revision identity captured at write time under the same Company/Tenant row lock. `recorded_at` remains audit time; timestamp alone is not proof of serialized ordering.

**Scope**
- Phase 4 Accounting OFF settlement, correction, and application-reallocation permissions.

**Preserve unchanged**
- The settlement exception grants no new root Income/Expense, account/category, opening-balance, Transfer, or unrelated module action. Normal Company, role, Branch, target, cap, audit, and idempotency checks remain mandatory.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Phase 4 OFF correction wording that could classify every post-OFF application or correction-child target as forbidden. Ordinary settlement applications remain allowed for pre-OFF obligations; only correction/reallocation uses the narrower root-history gate.

**Implementation impact**
- The command boundary must distinguish normal Receipt/Payment settlement from correction/reallocation before applying the pre-OFF correction predicate.

### ADDITION — Company-level Accountant manages Investor Monthly Interim amount

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- Only a Company-level Accountant for the same Company may set or edit an Investor's fixed Monthly Interim amount, including through the Investor create/edit workflow.
- A Branch Accountant, Platform Back Office user, Owner, Investor, or user from another Company may not set or edit this amount. Branch selection does not grant this permission.

**Scope**
- Mutation of the Investment-owned Monthly Interim amount configuration for an Investor belonging to the actor's Company.

**Preserve unchanged**
- Company isolation, server-side role checks, Branch boundaries for other Investment actions, Owner read-only rules, and Platform Back Office authority over other protected configuration remain unchanged. This is not a generic Company Accountant permission for other Investor settings or modules.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: Platform Back Office is the sole administrator of Monthly Interim rate configuration and Accountants cannot change it, only for the new fixed Monthly Interim amount field. Platform Back Office authority over all other protected rates/configuration is unchanged.

**Implementation impact**
- Enforce the same-Company Company-level Accountant grant at the backend mutation boundary for this field; do not infer authority from a selected Branch or expose a Platform Back Office override.

## Phase 5 Approved Business Decision Additions — Investor and Vehicle permissions

### ADDITION — Investment and Vehicle permissions are action-specific

**Status:** APPROVED BUSINESS DECISION<br>
**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may create/edit a same-Company Investor profile. Investor profile identity is Company-wide; this grants no access to another Branch's Fund credits or balances.
- Fund credit creation: Branch Accountant may post only for an assigned authorized Branch; Company-level Accountant may post for any Branch in the same Company.
- Fund credit reads: Branch Accountant sees only their own authorized Branch credits and amounts, and no consolidated Company Fund balance; Company-level Accountant may see the consolidated ledger.
- Only Company-level Accountant may use pooled Fund to fund a Vehicle purchase.
- Vehicle create/edit is limited to an authorized current Branch for Branch Accountant; Company-level Accountant may operate on any Branch in the same Company.
- Vehicle Branch movement is Company-level Accountant only. Cross-Branch permission is limited to Vehicle Management.
- Principal return: Branch Accountant may return eligible Available Fund from their own Branch source; Company-level Accountant may return eligible Available Fund from any same-Company Branch.
- Loss confirmation/Profit offset is a separate Investment action: Branch Accountant may act only for their authorized Branch; Company-level Accountant may act across same-Company Branches. Full Exit calculation across Branches and final settlement are Company-level Accountant only.
- Vehicle deactivation/registration reuse must remain unavailable until authoritative Sold, open Job and open-finance/settlement sources exist. When enabled later, Branch Accountant is restricted to own Branch; Company-level Accountant may act across same-Company Branches after all guards pass.

**Scope**
- Investor profile, Fund credit/use/return, Vehicle create/edit/move/deactivation, and later Investment Loss/Exit permissions.

**Preserve unchanged**
- Branch selection is never authorization. Every action rechecks active same-Company membership, role grants and effective Branch assignments server-side. No permission here changes Garage, Sales, Accounting, or other module authority. Owner remains read-only.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED/STALE STATEMENT: the Phase 5 BDRs for Investor profile editing, Fund credit/use/read/return Branch scope, Vehicle funding, Vehicle movement, Loss offset authority, and Exit settlement actor. This does not grant generic cross-Branch access or release the future module dependencies for deactivation.

**Implementation impact**
- Add action-specific policy keys and query filters; derive branch scope from server-side grants rather than caller-selected Branch IDs.

### ADDITION — Seller payable installments follow Branch accounting scope

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record actual installments only for seller payables attributed to their authorized Branch.
- A same-Company Company-level Accountant may record installments for any Branch.

**Scope**
- Actual payment of a Phase 5 Vehicle Purchase seller payable.

**Preserve unchanged**
- Only Company-level Accountant may create a Vehicle purchase using pooled Investor Fund. This installment permission does not authorize a new purchase, Fund-use, or generic cross-Branch action.

**Supersedes**
- None; the seller-payment actor scope was not previously specified.

**Implementation impact**
- Enforce purchase Branch scope from server grants; do not trust a Branch ID supplied by the client.

### ADDITION — Company-wide automation approval setting authority

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- Only the same-Company Company-level Accountant may switch Company-wide Automation Approval ON or OFF.
- Branch Accountants, Owners, and Platform Back Office cannot manage this setting.

**Scope**
- Company-wide automation configuration across every module.

**Preserve unchanged**
- An Accountant's setting authority does not grant them an operation-specific permission they do not already hold; Owner remains read-only for ordinary Company mutations.

**Supersedes**
- None; this defines a new configuration permission without widening existing posting permissions.

**Implementation impact**
- Authorize using the active same-Company Company-level Accountant grant, never a client-selected role or Branch context.

### ADDITION — Post-Exit Profit-restatement overpayment disposition authority

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may choose to keep open or waive an unpaid historical Investor Profit restatement overpayment only for an adjustment attributed to their authorized Branch.
- A Company-level Accountant may choose for any such adjustment within the same Company.

**Scope**
- Role authority for the case-specific post-Exit disposition of an unoffset Investor Profit overpayment caused by historical restatement.

**Preserve unchanged**
- This authority applies only to that Investment adjustment. It is not a generic cross-Branch permission. Company-level Accountant authority to finalize a cross-Branch Investor Exit remains unchanged. Owner and Platform Back Office receive no new authority.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which role may select the post-Exit overpayment disposition.

**Implementation impact**
- Validate the adjustment's original source Branch and Company server-side; do not trust a client-selected Branch or role.

### ADDITION — Authority to record repayment after Exit

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record actual repayment against an open post-Exit Investor Profit restatement adjustment only when the adjustment belongs to their authorized source Branch.
- A Company-level Accountant may record that repayment for any Branch within the same Company.

**Scope**
- Role permission for actual cash collection against an open post-Exit overpayment adjustment.

**Preserve unchanged**
- Company isolation and BranchAssignment scope remain enforced. This does not grant generic cross-Branch Accounting or other-module permission and does not let a Branch Accountant finalize a cross-Branch Exit.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: who may record actual repayment against an open post-Exit restatement adjustment.

**Implementation impact**
- Validate the adjustment's original source Branch and Company through server-side grants before posting; client-selected Branch is not authorization.

### ADDITION — Fund Credit attribution-correction authority

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may correct a wrong-Investor Fund Credit only when the original Fund Credit belongs to their authorized source Branch.
- A Company-level Accountant may correct Fund Credits from any Branch within the same Company.

**Scope**
- The Investment-specific append-only correction that moves a valid Fund Credit's attribution from one Investor to another without adding or changing an actual Cash/Bank movement.

**Preserve unchanged**
- Company isolation, Branch source provenance, default-deny, and all existing role limits. This grants no generic cross-Branch permission for Garage, Vehicle, Accounting, Sales or other modules. Owner and Platform Back Office receive no new authority.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED STATEMENT: which role may authorize a wrong-Investor Fund Credit attribution correction.

**Implementation impact**
- Check the authenticated role's Company and authorized source Branch against the original Fund Credit on the server. Do not derive correction permission from the destination Investor or a submitted Branch ID.

### ADDITION — Branch scope for Stock Vehicle Buyer refunds

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record an actual Buyer refund only for a Sale in their authorized Branch.
- A Company-level Accountant may record an actual Buyer refund for any Branch within the same Company.

**Scope**
- Actual Cash/Bank refunds linked to a Stock Vehicle Sale's Buyer refund obligation.

**Preserve unchanged**
- Enforce Company isolation and the Sale's original Branch. This rule applies only to Stock Vehicle Buyer refunds and grants no generic cross-Branch permission to Sales, Garage, Vehicle, Investment, Accounting, or other actions.

**Supersedes**
- None; this specifies the previously unset Branch scope for actual Stock Vehicle Buyer refunds.

**Implementation impact**
- Authorize against the Sale and refund source Branch from server-side records; do not trust a submitted Branch ID or the Cash/Bank account selection as permission.

### ADDITION — Branch scope for Sale confirmation and Buyer Receipts

**Status:** APPROVED BUSINESS DECISION

**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may create and confirm a Sale, and record its Buyer Receipts, only for a Sale in their authorized Branch.
- A Company-level Accountant may create/confirm Sales and record Buyer Receipts for any Branch within the same Company.

**Scope**
- Creation/confirmation of a Stock Vehicle Sale and recording actual Buyer Receipts against that Sale.

**Preserve unchanged**
- Buyer Receipts remain separate actual Cash/Bank events. Q84's Buyer refund permission remains as recorded. This decision grants no generic cross-Branch permission to Sales, Garage, Vehicle, Investment, Accounting, or other actions.

**Supersedes**
- None; this sets the Branch boundary for Sale confirmation and Buyer Receipts without changing Q84's separate Buyer refund rule.

**Implementation impact**
- Derive Company and source Branch from the Sale/Vehicle on the server for each create and receipt command; ignore client-supplied Branch as authorization.

### ADDITION — Sale price correction follows the Sale's Branch permission

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may correct a confirmed Sale only within their authorized Branch. A same-Company Company-level Accountant may correct a Sale from any Branch in that Company.

**Scope**
- Audited correction of agreed price on a confirmed Stock Vehicle Sale.

**Preserve unchanged**
- Q85 Sale creation/confirmation and Buyer Receipt permissions remain unchanged. No generic cross-Branch permission is granted to Garage, Vehicle, Investment, Accounting, or other modules.

**Supersedes**
- None; this extends Q85's Sale-specific Branch scope to Sale price corrections only.

**Implementation impact**
- Authorize against the server-owned Sale Company and Branch; ignore any client-submitted Branch as a grant.

### ADDITION — Branch authority for Vehicle Expense actions (Q112–Q114)

**Status:** APPROVED BUSINESS DECISION
**Effective documentation state:** Current V2 addition

**Rule**
- A Branch Accountant may record direct Stock Vehicle expenses and their actual installments only for Vehicles in the Accountant's authorized Branch.
- A Branch Accountant may record an actual Vendor refund or correct a Vehicle Expense/source allocation only for the affected Vehicle in the Accountant's authorized Branch.
- A same-Company Company-level Accountant may perform each of these actions for any Branch in that Company.

**Scope**
- Direct Vehicle Expense creation, actual installment payments, actual Vendor refunds, and cost/source-allocation corrections.

**Preserve unchanged**
- These are Vehicle-specific grants. They do not grant generic cross-Branch authority in other modules. Company isolation and server-side BranchAssignment checks remain mandatory.

**Supersedes**
- None; this sets the Vehicle Expense Branch scope for these actions.

**Implementation impact**
- Authorize each mutation against the persisted Vehicle's Company and Branch, not a client-supplied Branch value.

### ADDITION — Phase 5 pooled Fund and Vehicle cost authority (Q125–Q131)

- Only a same-Company Company-level Accountant may allocate pooled Investor Fund to a Vehicle Purchase or Investor-linked direct Vehicle Expense, across that Company's Branches.
- A Branch Accountant may create a Company Running Capital-only Purchase or Expense only for a Vehicle in their authorized Branch. A Company-level Accountant may act in any Branch of the same Company.
- Investor-linked Vehicle Expense creation, including the complete Fund-first/Running Capital allocation, is Company-level Accountant-only; there is no Branch-created pending draft.
- For an excess Vehicle Expense refund classified as Company Income, the authorized Accountant must create the separate Income record and Receipt using normal Company/Branch permissions. Never modify an old Income event or bypass Income/Receipt permissions.

### ADDITION — Branch authority for ordinary Investor Vehicle Profit payments

**Status:** APPROVED BUSINESS DECISION — 2026-11-19

**Rule**
- A Branch Accountant may record an actual ordinary Investor Vehicle Profit payment only for a Sale in the Accountant's authorized Branch.
- A same-Company Company-level Accountant may record that payment for a Sale in any Branch of the Company.
- This is an action-specific Branch grant. It does not grant cross-Branch Investor/Fund access, reconciliation correction, Loss confirmation, Exit settlement, or other financial mutation authority.
- Payment remains a human-confirmed actual Accounting Payment linked to the approved Investor Profit entitlement; a calculation or approval alone is not Paid.

**Scope**
- Actual payment of confirmed positive deal-level Investor Vehicle Profit.

**Preserve unchanged**
- The payment reduces the Sale-date Investor period's outstanding entitlement once. Company and Branch, source Sale, current module state, available amount after applicable approved offsets, and Accounting movement are validated server-side.

**Supersedes**
- SUPERSEDES EARLIER UNRESOLVED Phase 8 wording that ordinary Investor Profit payment authority still needed a business answer.

**Implementation impact**
- Use a dedicated payout action permission and Sale Branch authorization. Keep the Company-level-only authority for pooled Fund use, Loss confirmation and cross-Branch corrections separate.

### ADDITION — Branch authority for Monthly Interim payments

**Status:** APPROVED BUSINESS DECISION — 2026-11-19

- A Branch Accountant may record an actual Monthly Interim payment only in their authorized payment Branch.
- A same-Company Company-level Accountant may record that payment in any Branch of the Company.
- This action-specific grant does not provide consolidated Fund visibility or cross-Branch permission for other actions. The actual Cash/Bank movement still requires normal Accounting authorization.

### ADDITION — Investor portal account binding (2026-11-19)

**Status:** APPROVED BUSINESS DECISION. Private portal access remains blocked until the backend binding and checks exist.

- A same-Company Company-level Accountant verifies and links an authenticated login account to an Investor profile in that Company. Only one active Investor profile may be linked to that account in the Company, and one Investor profile may have only one active login account.
- Link, replacement and revocation retain actor/time/history. Neither name/phone similarity nor an Investor role grant alone establishes record ownership. The server must resolve an active binding before returning private Investor data or accepting an Investor self-service request.
- Company isolation, active membership, Investor role, Investor status and applicable module gates still apply. A revoked binding immediately removes self-service access; no historical financial record is deleted.

**Supersedes:** The unresolved account-to-Investor binding authority and cardinality for Phase 10 only; it does not grant Investor financial mutation rights.
