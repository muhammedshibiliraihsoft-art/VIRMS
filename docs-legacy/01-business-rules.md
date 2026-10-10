> ⚠️ LEGACY — NON-AUTHORITATIVE — DO NOT IMPLEMENT

> This document is retained only for historical reference.
> `/docs-final/` is the sole VIRMS implementation source of truth.
> Any older `LOCKED`, `FINAL`, or `AUTHORITATIVE` wording below is historical
> and is superseded by the current `/docs-final/` documentation.

01 — BUSINESS RULES
Vehicle Investment, Modification & Resale Management System
Version: Final v0.4
Status: LOCKED — SOURCE OF TRUTH
Purpose: Database, API, Permissions, Finance Logic, UI, Security, Testing, Audit, Deployment എന്നിവയ്ക്ക് authoritative business-rule reference.
ഈ document-ൽ LOCKED എന്ന് നൽകിയ rules implementation സമയത്ത് invent, reinterpret, silently change, അല്ലെങ്കിൽ omit ചെയ്യരുത്.
BUSINESS DECISION REQUIRED എന്ന് നൽകിയ കാര്യങ്ങൾ മാത്രം പിന്നീട് business confirmation ആവശ്യമാണ്.
Version 1 ആണ് base source of truth. പിന്നീട് explicitly confirmed ചെയ്ത business changes മാത്രമാണ് അതിനെ override ചെയ്യുന്നത്.

A. CORE BUSINESS MODEL
BR-CORE-001 — External Investor Funding
Status: LOCKED
Business-ന്റെ പ്രധാന funding source External Investors ആണ്.
Owner 1 / Owner 2 എന്നിവരെ normal investor/funding source ആയി current business model-ൽ കണക്കാക്കരുത്.

BR-CORE-002 — Core Vehicle Business Cycle
Status: LOCKED
Business flow:
Investor Fund
→ Vehicle Purchase
→ Repair / Modification / Work
→ Vehicle Sale
→ Principal Recovery
→ Profit Distribution

BR-CORE-003 — Vehicle-Level Profitability
Status: LOCKED
ഓരോ vehicle-ന്റെയും profitability independently track ചെയ്യണം.
Formula
Purchase Cost + Vehicle Expenses = Total Vehicle Cost
Agreed Sale Price − Total Vehicle Cost = Profit / Loss

B. INVESTOR RULES
BR-INV-001 — One Vehicle, One Investor
Status: LOCKED — CRITICAL
ഒരു vehicle-ന് ഒരൊറ്റ investor മാത്രമേ ഉണ്ടാകാവൂ.
Two investors must never fund the same vehicle.
ഈ rule UI-ൽ മാത്രം അല്ല; backend/database business logic level-ലും enforce ചെയ്യണം.

BR-INV-002 — One Investor, Multiple Vehicles
Status: LOCKED
ഒരു investor-ന്റെ fund ഉപയോഗിച്ച് ഒന്നിലധികം vehicles fund ചെയ്യാം.
Fixed vehicle-count limit ഉണ്ടാകരുത്.

BR-INV-003 — Investor Fund Position
Status: LOCKED
ഓരോ investor-നും system താഴെപ്പറയുന്ന financial position track ചെയ്യണം:
Total Fund
Available Fund
Fund Currently Used in Vehicles
Recovered Principal
Profit Earned
Profit Paid
Profit Pending

BR-INV-004 — Unlimited Investor Support
Status: LOCKED
System investor count hard-code ചെയ്യരുത്.
Future-ൽ ആവശ്യത്തിന് പുതിയ investors add ചെയ്യാൻ കഴിയണം.

BR-INV-005 — Investor History Preservation
Status: LOCKED
Investor inactive / closed ആയാലും പഴയ:
Fund Transactions
Vehicles
Expenses
Sales
Profit
Settlements
Exit Records
delete ചെയ്യരുത്.

BR-INV-006 — Investor Lifecycle
Status: LOCKED
System investor lifecycle support ചെയ്യണം:
Active
→ Exit Requested
→ Settlement Pending
→ Closed
Operational requirement ഉണ്ടെങ്കിൽ Inactive status support ചെയ്യാം.
Historical identity preserve ചെയ്യണം.

BR-INV-007 — Investor Can Return Later
Status: LOCKED PRINCIPLE
Previously closed investor future-ൽ വീണ്ടും business relationship തുടങ്ങാൻ system architecture support ചെയ്യണം.
Old financial/history records overwrite ചെയ്യരുത്.

C. PRINCIPAL & INVESTOR FUND RULES
BR-FUND-001 — Principal and Profit Must Be Separate
Status: LOCKED — CRITICAL
Investor-ന്റെ original principal/fundയും investor profit shareഉം ഒരേ balance ആയി mix ചെയ്യരുത്.
Principal ≠ Profit

BR-FUND-002 — Investor Funds Full Vehicle Cost
Status: LOCKED — CRITICAL
Investor vehicle purchase price മാത്രം fund ചെയ്യുന്നതല്ല.
Vehicle വാങ്ങിയതുമുതൽ vehicle sale-ready ആകുന്നതുവരെ ആ vehicle-നായി വരുന്ന approved vehicle costs എല്ലാം അതേ investor-ന്റെ fund-ൽ നിന്നാണ് ഉപയോഗിക്കേണ്ടത്.
Includes:
Purchase
Repair
Modification
Paint
Engine Work
Mechanical Work
Parts
Labour Expense
Transport
Documentation
Other Approved Vehicle Expenses
Formula
Vehicle Capital Used = Purchase Cost + Approved Vehicle Work Expenses

BR-FUND-003 — Available Balance Can Remain Unused
Status: LOCKED
Vehicle purchase/work കഴിഞ്ഞ് investor fund-ൽ balance ഉണ്ടെങ്കിൽ അത് Available Balance ആയി അവിടെ തന്നെ നിലനിൽക്കാം.
അതിനെ നിർബന്ധമായി മറ്റൊരു vehicle-ൽ ഉപയോഗിക്കേണ്ടതില്ല.

BR-FUND-004 — Additional Fund Option
Status: LOCKED
Existing investor-ന് future-ൽ additional capital add ചെയ്യാനുള്ള option system-ൽ ഉണ്ടായിരിക്കണം.
Additional fund add ചെയ്യുന്നത് mandatory അല്ല.
ഓരോ fund addition-നും transaction/history preserve ചെയ്യണം.

BR-FUND-005 — Recovered Principal Returns to Investor Fund
Status: LOCKED
Vehicle sale വഴി capital recover ചെയ്താൽ applicable recovered principal അതേ investor-ന്റെ fund position-ലേക്ക് തിരികെ വരണം.
Investor active ആണെങ്കിൽ അത് future vehicle funding-നായി reuse ചെയ്യാം.
Recovered principal automatically cash/bank payout ആയി കണക്കാക്കരുത്.

BR-FUND-006 — Profit Is Not New Principal
Status: LOCKED
Vehicle sale-ൽ ലഭിക്കുന്ന investor profit automatically principal/reinvestment fund-ലേക്ക് merge ചെയ്യരുത്.
Profit separate balance / settlement flow ആയി maintain ചെയ്യണം.

BR-FUND-007 — No Normal Negative Fund in Current UI
Status: LOCKED
Current frontend workflow-ൽ investor available fund-നെക്കാൾ കൂടുതൽ vehicle purchase/work expense create ചെയ്ത് negative fund ഉണ്ടാക്കാനുള്ള normal option expose ചെയ്യരുത്.
Current operational flow available fund പരിധിക്കുള്ളിൽ പ്രവർത്തിക്കണം.

BR-FUND-008 — Future Negative-Fund Support Must Not Be Blocked
Status: LOCKED ARCHITECTURAL REQUIREMENT
Future business requirement വന്നാൽ protected negative-fund / override capability backend architecture support ചെയ്യാൻ കഴിയണം.
Current frontend-ൽ അത് കാണിക്കരുത്.
Future enablement deliberate protected business change ആയിരിക്കണം.

D. VEHICLE RULES
BR-VEH-001 — System Identity
Status: LOCKED
Vehicle-ന്റെ system identity human-readable name അല്ലെങ്കിൽ registration number മാത്രം ആശ്രയിക്കരുത്.
Backend-generated unique ID ആണ് immutable system identity.
Registration number is a business attribute and must not be treated as the immutable system identifier.

BR-VEH-002 — Investor Mapping
Status: LOCKED
Vehicle create/purchase സമയത്ത് funding investor record ചെയ്യണം.
ഒരു സമയത്ത്:
One Vehicle → One Investor

BR-VEH-003 — Vehicle Financial History
Status: LOCKED
Vehicle-നോട് ബന്ധപ്പെട്ട full financial history preserve ചെയ്യണം.
Includes:
Purchase
Repair
Modification
Labour
Parts
Transport
Documentation
Other Approved Expenses
Sale
Buyer Payments
Profit / Loss

BR-VEH-004 — Vehicle Status Lifecycle
Status: BUSINESS DECISION REQUIRED
Possible initial lifecycle:
Purchased → In Work → Ready → Listed → Sold
Exact statuses / names 05 — Vehicle / Investor / Finance Workflow-ൽ final lock ചെയ്യണം.

BR-VEH-005 — Sold Vehicle History
Status: LOCKED
Sold vehicle record hard-delete ചെയ്യരുത്.
Sale-related financial corrections traceable ആയിരിക്കണം.

E. VEHICLE EXPENSE RULES
BR-EXP-001 — Every Vehicle Expense Must Belong to That Vehicle
Status: LOCKED
Vehicle-നായി വരുന്ന expense add ചെയ്യുമ്പോൾ അത് ഏത് vehicle-നാണ് വന്നതെന്ന് system record ചെയ്യണം.
Example:
Vehicle A
Paint — ₹20,000
Engine Work — ₹35,000
Labour — ₹15,000
Total Vehicle Expense = ₹70,000

BR-EXP-002 — Vehicle Expense Uses That Investor's Fund
Status: LOCKED — CRITICAL
Vehicle-specific approved expense അതേ vehicle-ന്റെ investor fund availability-ൽ നിന്നാണ് deduct ചെയ്യേണ്ടത്.

BR-EXP-003 — Individual Expense Entries
Status: LOCKED
ഓരോ vehicle expense entryയും separately history/list ആയി കാണാൻ കഴിയണം.

BR-EXP-004 — Total Vehicle Expense
Status: LOCKED
Individual expense entries ഉണ്ടായാലും vehicle summary-ൽ:
Total Vehicle Expense
clear ആയി കാണണം.
Category-wise totals കാണിക്കാം.
Example:
Paint Total
Engine Work Total
Labour Total
Parts Total
Other Total

BR-EXP-005 — No Per-Labourer Cost Breakdown Required
Status: LOCKED
Vehicle expense calculation-നായി ഓരോ labourer-നും individually cost split ചെയ്യേണ്ടതില്ല.
Multiple workers ഒരേ vehicle-ൽ ജോലി ചെയ്താലും vehicle costing-ൽ:
Labour Expense = Total Work-Level Labour Expense
എന്ന് record ചെയ്താൽ മതി.

BR-EXP-006 — Dynamic Expense Categories
Status: LOCKED
Expense categories permanently hard-coded fixed list ആയി നിൽക്കരുത്.
Account system manage ചെയ്യുന്ന Accountant/Admin-ന് frontend UI വഴി പുതിയ expense category add ചെയ്യാൻ കഴിയണം.
Initial examples:
Repair
Modification
Labour
Parts
Paint
Transport
Documentation
Miscellaneous
Future category add ചെയ്യാൻ code deployment ആവശ്യമില്ല.

BR-EXP-007 — Financial Correction History
Status: LOCKED
Financial expense record തെറ്റിയാൽ silently overwrite/delete ചെയ്യരുത്.
Correction history / audit trail maintain ചെയ്യണം.

F. PROFIT DISTRIBUTION RULES
BR-PROFIT-001 — Investor Profit Share Is Per Investor
Status: LOCKED — CRITICAL
Investor profit percentage global fixed percentage അല്ല.
ഓരോ investor account/agreement setup സമയത്ത് ആ investor-ന്റെ agreed profit-share percentage set ചെയ്യണം.
Examples:
Investor A = 33%
Investor B = 20%
Investor C = 40%
33% universal hard-coded rule അല്ല.

BR-PROFIT-002 — Owners Pool Is the Remainder
Status: LOCKED
Formula
Owners Pool % = 100% − Investor Share %
Examples:
Investor 33% → Owners Pool 67%
Investor 20% → Owners Pool 80%
Investor 40% → Owners Pool 60%

BR-PROFIT-003 — Current Owner Internal Split
Status: LOCKED CURRENT BUSINESS VALUE
Current standard owner split:
Owner 1 = 48.5% of Owners Pool
Owner 2 = 51.5% of Owners Pool
ഇത് total vehicle profit-ന്റെ direct percentage അല്ല.
ആദ്യം investor share calculate ചെയ്യണം.
ശേഷിക്കുന്ന Owners Pool ആണ് 48.5% / 51.5% ആയി split ചെയ്യേണ്ടത്.

BR-PROFIT-004 — Profit Calculation Example
Status: LOCKED LOGIC
Vehicle Profit = ₹1,00,000
Investor Share = 33%
Investor:
₹33,000
Owners Pool:
₹67,000
Owner 1:
₹67,000 × 48.5% = ₹32,495
Owner 2:
₹67,000 × 51.5% = ₹34,505

BR-PROFIT-005 — Percentages Must Not Be Hard-Coded
Status: LOCKED — CRITICAL
Source code-ൽ hard-code ചെയ്യരുത്:
Investor Profit Share
Owner Internal Split
Applicable Garage-Specific Percentage Configuration
Business configuration വഴി manage ചെയ്യാൻ കഴിയണം.

BR-PROFIT-006 — Protected Profit Rule Editing
Status: LOCKED — SECURITY CRITICAL
Existing protected profit distribution rules change ചെയ്യാൻ:
Authorized Main Owner/Admin only
Accountant അല്ലെങ്കിൽ സാധാരണ users protected profit settings edit ചെയ്യാൻ പാടില്ല.

BR-PROFIT-007 — Separate Protected Password
Status: LOCKED — SECURITY CRITICAL
Protected percentage configuration change ചെയ്യാൻ normal login password-ൽ നിന്ന് വേറിട്ട separate security password ആവശ്യമാണ്.
Accountant/other users ഈ password അറിയാൻ പാടില്ല.

BR-PROFIT-008 — Initial Investor Percentage Setup
Status: TO DEFINE IN 02 — USER ROLES & PERMISSIONS
Investor account/agreement create ചെയ്യുമ്പോൾ agreed investor percentage enter/approve ചെയ്യേണ്ട exact role/approval flow Roles & Permissions section-ൽ define ചെയ്യണം.
Existing percentage change protected action ആയിരിക്കും.

BR-PROFIT-009 — Profit Rule Change Audit
Status: LOCKED
Percentage change വന്നാൽ preserve ചെയ്യണം:
Old Value
New Value
Applicable Scope
Changed By
Changed Date/Time

BR-PROFIT-010 — Historical Percentage Snapshot
Status: LOCKED — CRITICAL
Current profit percentage settings future-ൽ change ചെയ്താലും already completed historical vehicle deals പുതിയ percentage ഉപയോഗിച്ച് recalculate ചെയ്യരുത്.
ഓരോ completed deal-നും അന്ന് applicable ആയ:
Investor Share %
Owner 1 %
Owner 2 %
Applicable Garage Configuration
historical snapshot ആയി preserve ചെയ്യണം.

G. GARAGE RULES
BR-LOC-001 — Current Business Has Two Garages
Status: LOCKED
Current business-ൽ 2 garages ഉണ്ട്.
Shop concept ഈ system-ന് ആവശ്യമില്ല.

BR-LOC-002 — Future Garage Expansion
Status: LOCKED
Garage 1 / Garage 2 code-ൽ hard-code ചെയ്യരുത്.
Future-ൽ additional garages UI/admin management വഴി add ചെയ്യാൻ കഴിയണം.

BR-LOC-003 — One Central System for All Garages
Status: LOCKED
ഓരോ garage-നും separate software ഉണ്ടാകില്ല.
എല്ലാ garages-ഉം ഒരേ central system ആണ് ഉപയോഗിക്കുന്നത്.
Owners/authorized users consolidated business view ലഭിക്കണം.

BR-LOC-004 — Garage-Specific Operational Data
Status: LOCKED
Garage അനുസരിച്ച് താഴെപ്പറയുന്ന data വ്യത്യാസപ്പെടാം:
Labour / Staff
Vehicles
Expenses
Work
Operational Records
Applicable Percentage Configuration

BR-LOC-005 — Garage-Specific Owner Split Support
Status: LOCKED
Current standard owner split 48.5% / 51.5% ആണെങ്കിലും future-ൽ garage അനുസരിച്ച് applicable owner percentages മാറാനുള്ള architecture support ചെയ്യണം.
Owner split global hard-coded value ആകരുത്.

BR-LOC-006 — Vehicle Current Garage
Status: LOCKED
Vehicle ഇപ്പോൾ ഏത് garage-ലാണ് ഉള്ളത് എന്ന് track ചെയ്യണം.

BR-LOC-007 — Garage Transfer History
Status: LOCKED
Vehicle ഒരു garage-ൽ നിന്ന് മറ്റൊരു garage-ലേക്ക് move ചെയ്താൽ പഴയ garage history overwrite ചെയ്ത് നഷ്ടപ്പെടുത്തരുത്.
Transfer history preserve ചെയ്യണം.

H. LABOUR / STAFF RULES
BR-LAB-001 — Labour Management
Status: LOCKED
System labour/staff management support ചെയ്യണം.

BR-LAB-002 — Labour Assignment
Status: LOCKED
Labour/staff member-നെ:
Garage
Vehicle
Work Type
എന്നിവയുമായി associate ചെയ്യാൻ കഴിയണം.

BR-LAB-003 — Labour Cost
Status: LOCKED
Vehicle work-ന്റെ total labour cost vehicle expense/cost calculation-ൽ include ചെയ്യണം.
Individual worker-level costing നിർബന്ധമല്ല.

BR-LAB-004 — Labour Work Status
Status: INITIAL MODEL — NOT FINAL
Suggested lifecycle:
Pending → In Progress → Completed
Final terminology 06 — Branch & Labour Architecture-ൽ confirm ചെയ്യണം.

BR-LAB-005 — Manual Salary / Payment Entry
Status: LOCKED
Current phase-ൽ fixed automated salary/payroll engine വേണ്ട.
Authorized user-ന് ആവശ്യമായപ്പോൾ manual salary/payment entry add ചെയ്യാൻ കഴിയണം.

BR-LAB-006 — Labour Payment Tracking
Status: LOCKED CAPABILITY
Labour payment information track ചെയ്യാൻ system support വേണം:
Total Charge / Amount
Paid Amount
Pending Amount
Payment Date
Payment Status
Current phase-ൽ salary automation നിർബന്ധമല്ല.

BR-LAB-007 — Future Salary Automation
Status: FUTURE SCOPE
Attendance, salary automation, payroll automation future phase-ൽ add ചെയ്യാം.
Current architecture future automation block ചെയ്യരുത്.

I. VEHICLE SALE & PAYMENT RULES
BR-SALE-001 — Full and Partial Payment Sales Are Allowed
Status: LOCKED
Vehicle:
Full Payment
Partial Payment
Credit Sale
basis-ൽ sell ചെയ്യാം.
Full amount കിട്ടിയിട്ടില്ലെങ്കിലും sale record create ചെയ്യാം.

BR-SALE-002 — Agreed Total Sale Price
Status: LOCKED
Profit calculation buyer ഇതിനകം paid ചെയ്ത amount അടിസ്ഥാനമല്ല.
Agreed Total Sale Price ആണ് calculation base.

BR-SALE-003 — Partial Payment Tracking
Status: LOCKED
Partial sale ആണെങ്കിൽ system track ചെയ്യണം:
Total Sale Price
Amount Received
Amount Pending / Receivable
Formula
Pending Amount = Total Sale Price − Amount Received

BR-SALE-004 — Profit Calculation Uses Full Agreed Sale Price
Status: LOCKED
Full payment കിട്ടാത്ത സാഹചര്യത്തിലും agreed total sale price അടിസ്ഥാനമാക്കി calculate ചെയ്യണം:
Vehicle Profit / Loss
Investor Share
Owners Pool
Owner 1 Share
Owner 2 Share

BR-SALE-005 — Pending Financial State
Status: LOCKED
Buyer full payment complete ചെയ്യാത്ത വരെ applicable collection/share state:
Pending / Receivable
ആയി കാണണം.
UI-ൽ pending financial state yellow / warning indication ഉപയോഗിച്ച് distinguish ചെയ്യാം.

BR-SALE-006 — Full Payment Completion
Status: LOCKED
Buyer total sale amount മുഴുവനായി pay ചെയ്താൽ payment status:
Fully Received / Paid
ആയി update ചെയ്യണം.
Pending receivable zero ആയിരിക്കണം.

BR-SALE-007 — Vehicle Financial Detail View
Status: LOCKED
Authorized vehicle details view-ൽ കുറഞ്ഞത് കാണണം:
Total Sale Price
Amount Received
Amount Pending
Total Vehicle Cost
Total Vehicle Expense
Calculated Profit / Loss
Investor Share
Owners Pool
Owner 1 Share
Owner 2 Share
Payment Status

BR-SALE-008 — Accounting / Receivables View
Status: LOCKED
Partial-payment information vehicle details screen-ൽ മാത്രം നിൽക്കരുത്.
Accounting/Receivables section-ലും separately കാണണം:
Vehicle
Buyer
Total Sale Price
Received Amount
Pending Amount
Payment Status

J. PROFIT SETTLEMENT RULES
BR-SET-001 — Profit Is Calculated Per Vehicle
Status: LOCKED
Profit monthly aggregate അടിസ്ഥാനമല്ല.
ഓരോ vehicle sale-നും independently calculate ചെയ്യണം.

BR-SET-002 — Vehicle-Level Profit Distribution
Status: LOCKED
Vehicle profit calculation sequence:
Profit / Loss
Investor Share
Remaining Owners Pool
Owner 1 Share
Owner 2 Share

BR-SET-003 — Partial Sale Profit State
Status: LOCKED
Agreed sale price അടിസ്ഥാനമാക്കി full profit/share calculate ചെയ്യാം.
Buyer full payment കിട്ടാത്ത വരെ corresponding financial collection state pending ആയി കാണണം.

BR-SET-004 — Partial Sale Principal Recovery Timing
Status: BUSINESS DECISION REQUIRED
Partial buyer payment വന്നപ്പോൾ investor principal എപ്പോൾ reusable Available Fund ആകണം എന്നത് final finance workflow-ൽ തീരുമാനിക്കണം.
Possible models:
A. Actually received amount അനുസരിച്ച് principal gradually recover ചെയ്യുക.
B. Full buyer payment complete ചെയ്തശേഷം principal fully recover ചെയ്യുക.
System ഒരിക്കലും unreceived money actual available cash/fund ആയി treat ചെയ്യരുത്.

K. INVESTOR EXIT RULES
BR-EXIT-001 — Three-Month Exit Notice
Status: LOCKED
Normal investor exit request-ന്:
3 months notice period mandatory

BR-EXIT-002 — Exit Terms & Conditions
Status: LOCKED
Investor exit request submit ചെയ്യുന്നതിനുമുമ്പ് Investor UI-ൽ Terms & Conditions clear ആയി കാണിക്കണം.
At minimum explain ചെയ്യണം:
3-month notice requirement
Existing vehicle commitments
Locked fund conditions
Unsold vehicle condition
Settlement process
Final closure conditions
Investor acceptance record ചെയ്തശേഷം exit request submit ചെയ്യണം.

BR-EXIT-003 — No New Vehicle Purchase During Exit Notice
Status: LOCKED
Investor exit notice period ആരംഭിച്ച ശേഷം ആ investor-ന്റെ fund ഉപയോഗിച്ച് new vehicle purchase ചെയ്യരുത്.
Already-funded vehicles-ന്റെ approved work and existing financial obligations normal workflow അനുസരിച്ച് continue ചെയ്യാം.

BR-EXIT-004 — Exit Request Does Not Immediately Close Account
Status: LOCKED
Exit request submit ചെയ്ത ഉടനെ investor account close ചെയ്യരുത്.
Investor settlement lifecycle-ലേക്ക് പോകണം.

BR-EXIT-005 — Unsold Vehicle Capital Can Remain Locked
Status: LOCKED — CRITICAL
Notice period കഴിഞ്ഞാലും investor capital unsold vehicle-ൽ locked ആണെങ്കിൽ business ഉടനെ ആ fund repay ചെയ്യേണ്ടതില്ല.
Existing vehicle sell/recover ചെയ്തശേഷം corresponding fund settle ചെയ്യാം.

BR-EXIT-006 — Closure After Vehicle Recovery
Status: LOCKED
Exit process സമയത്ത് existing vehicle sale/recovery പൂർത്തിയായ ശേഷം:
Principal
Applicable Profit
Pending Receivables
Final Balance
settle ചെയ്ത് investor financially close ചെയ്യണം.

BR-EXIT-007 — Owner Exceptional Early Closure
Status: LOCKED
Special circumstances-ൽ authorized Owners-ന് 3-month notice period complete ആകുന്നതിന് മുമ്പ് early closure process initiate ചെയ്യാം.
ഇത് normal investor self-service option അല്ല.

BR-EXIT-008 — Early Closure Does Not Make Locked Capital Available
Status: LOCKED
Owner early closure initiate ചെയ്താലും unsold vehicle-ൽ locked capital immediately available ആയി കണക്കാക്കരുത്.
Actual financial recovery/available balance അടിസ്ഥാനത്തിലാണ് settlement.

L. BUYER / CUSTOMER RULES
BR-BUYER-001 — Basic Buyer Details
Status: LOCKED
Vehicle sale സമയത്ത് normal business-required buyer/customer details store ചെയ്യണം.

BR-BUYER-002 — Buyer Details Must Be Extendable
Status: LOCKED
Future-ൽ additional buyer details ആവശ്യമുണ്ടെങ്കിൽ architecture fields add/change ചെയ്യാൻ support ചെയ്യണം.

M. SOLD VEHICLE FINANCIAL CORRECTIONS
BR-CORR-001 — Accountant Correction Authority
Status: LOCKED
Sold vehicle financial record-ൽ legitimate correction ആവശ്യമുണ്ടെങ്കിൽ Accountant controlled correction നടത്താൻ കഴിയണം.

BR-CORR-002 — Corrections Must Be Audited
Status: LOCKED — CRITICAL
Correction എന്ന പേരിൽ old financial truth silently overwrite/delete ചെയ്യരുത്.
At minimum record ചെയ്യണം:
Previous Value
Corrected Value
Changed By
Date / Time
Reason where applicable

N. CASH / BANK ACCOUNT RULES
BR-ACC-001 — Cash and Bank Must Be Separate
Status: LOCKED
Cash and Bank balances ഒരൊറ്റ generic financial balance ആയി merge ചെയ്യരുത്.
Separate account-level tracking വേണം.

BR-ACC-002 — Individual Account Tracking
Status: LOCKED
ഓരോ Cash / Bank account-ന്റെയും:
Balance
Transactions
Receipts
Payments
separately track ചെയ്യണം.
Future-ൽ multiple accounts support ചെയ്യണം.

O. GST / TAX / INVOICE RULES
BR-TAX-001 — GST / Tax / Invoice Capability
Status: LOCKED
System architecture GST/Tax/Invoice-related information support ചെയ്യണം.

BR-TAX-002 — Not Mandatory Everywhere
Status: LOCKED
Phase 1-ൽ എല്ലാ vehicle/transaction record-നും GST/Tax fields compulsory ആക്കേണ്ടതില്ല.
Applicable business situations-ൽ മാത്രം ഉപയോഗിക്കാൻ കഴിയണം.

P. RECORD INTEGRITY & AUDIT RULES
BR-DATA-001 — No Silent Financial Deletion
Status: LOCKED — CRITICAL
Important financial history hard-delete / silent-delete ചെയ്യരുത്.

BR-DATA-002 — Financial Auditability
Status: LOCKED
Important business changes traceable ആയിരിക്കണം.
At minimum:
Investor Funds
Additional Fund Entries
Vehicle Purchases
Vehicle Expenses
Sales
Buyer Payments
Receivables
Investor Profit Shares
Owner Shares
Settlements
Financial Corrections
Protected Settings
Investor Early Closure

BR-DATA-003 — Historical Business Truth
Status: LOCKED
Current value/configuration update ചെയ്താലും past completed business events/history മാറരുത്.

BR-DATA-004 — Historical Calculation Configuration
Status: LOCKED — CRITICAL
Past vehicle deal-ൽ ഉപയോഗിച്ച percentages/configuration future settings change കാരണം മാറരുത്.
Historical financial calculations reproducible ആയിരിക്കണം.

Q. IMPORTANT CALCULATION RULES
Vehicle Capital Used
Purchase Cost + Approved Vehicle Expenses

Available Investor Fund
Total Investor Fund − Capital Currently Used + Applicable Recovered Principal

Vehicle Profit / Loss
Agreed Sale Price − Total Vehicle Cost

Investor Profit Share
Vehicle Profit × Investor-Specific Profit Share %

Owners Pool
Vehicle Profit × (100% − Investor Share %)

Owner 1 Share
Owners Pool × Applicable Owner 1 %
Current standard configuration:
48.5%

Owner 2 Share
Owners Pool × Applicable Owner 2 %
Current standard configuration:
51.5%

Partial Sale Pending Amount
Agreed Total Sale Price − Amount Received

R. REMAINING BUSINESS DECISIONS
Only the following business rules remain intentionally unresolved.
BDR-001 — Exact Vehicle Status Lifecycle
Exact vehicle operational stages/names later lock ചെയ്യണം.
Current example only:
Purchased → In Work → Ready → Listed → Sold

BDR-002 — Vehicle Loss Allocation
Vehicle sale result negative ആണെങ്കിൽ loss ആരാണ് bear ചെയ്യുന്നത് എന്നത് confirm ചെയ്തിട്ടില്ല.
Decide ചെയ്യേണ്ടത്:
Investor principal loss?
Owners bear the loss?
Shared loss?
Agreement-specific loss model?
ഈ rule implementation agent assume ചെയ്യരുത്.

BDR-003 — Partial Sale Principal Recovery Timing
Partial buyer payment സമയത്ത് investor principal reusable fund ആകുന്ന exact timing final finance workflow-ൽ lock ചെയ്യണം.
System unreceived amount available cash ആയി treat ചെയ്യരുത്.

S. ITEMS DEFINED IN LATER ARCHITECTURE DOCUMENTS
02 — User Roles & Permissions
Define:
Investor initial profit percentage setup authority
Protected percentage-change authority
Owner early-exit permission
Separate protected password workflow
Accountant exact operational permissions

04 — Data Model & Relationships
Define implementation structures for:
Investor Fund Ledger
Vehicle Capital Ledger
Expense Transactions
Buyer Receivables
Cash Accounts
Bank Accounts
Historical Percentage Snapshots
Audit / Correction Records

05 — Vehicle / Investor / Finance Workflow
Finalize:
Vehicle status lifecycle
Partial-sale principal recovery timing
Loss-allocation rule
Sale → Recovery → Profit → Settlement sequence

06 — Branch & Labour Architecture
Define:
Garage configuration
Garage-specific percentage configuration
Labour assignment
Manual salary/payment model

07 — UI / Navigation
Include:
Investor Exit Terms & Conditions
Pending/Receivable warning state
Vehicle Financial Details
Receivables View
Investor Fund Position
Cash / Bank account views

10 — Security Architecture
Define technical protection for:
Separate protected password
Profit percentage configuration
Financial correction audit
Investor early closure
Sensitive financial settings

T. LOCKED PRINCIPLES SUMMARY
Investor
Unlimited Investors
One Investor → Multiple Vehicles
Investor Lifecycle Preserved
Closed Investor History Preserved

Vehicle
One Vehicle → One Investor
Unique Backend ID
Registration Number = Business Attribute
Vehicle Financial History Preserved

Fund
Investor Funds Purchase + Full Vehicle Work Cost
Principal ≠ Profit
Profit Does Not Automatically Become Principal
Unused Fund Can Remain Available
Additional Fund Can Be Added
No Normal Negative Fund in Current Frontend
Recovered Principal Returns to Same Investor Fund

Profit
Investor Share = Per Investor
33% Is Not Universal
Owners Pool = Remaining Percentage
Current Standard Owner Split = 48.5% / 51.5%
Garage-Specific Owner Split Supported
Protected Settings Require Authorized Owner/Admin + Separate Password
Past Deals Preserve Their Original Percentage Snapshot

Garage
Current Garages = 2
No Shop Concept
Future Garages Can Be Added
All Garages Use One Central System
Garage-Specific Labour / Operations / Percentage Configuration Supported

Expenses
Every Vehicle Expense Belongs to That Vehicle
Vehicle Expense Uses That Vehicle Investor's Fund
Individual Expense History + Total Vehicle Expense
No Individual Labourer Cost Breakdown Required
Accountant/Admin Can Add Future Expense Categories from UI

Labour
Labour Can Be Assigned to Garage + Vehicle + Work Type
Vehicle Uses Total Labour Expense
Manual Salary/Payment Entry in Current Phase
Payroll Automation Can Come Later

Sales
Full + Partial/Credit Sales Supported
Profit Uses Full Agreed Sale Price
Received and Pending Amount Tracked Separately
Pending Financial State Visible Until Full Collection
Vehicle Details + Accounting Receivables Both Show Payment Position

Investor Exit
Normal Exit = 3 Months Notice
Terms & Conditions Before Exit Request
No New Vehicle Purchase During Exit Notice
Already-Funded Approved Vehicle Work Can Continue
Unsold Vehicle Capital Waits Until Recovery
Owners Can Trigger Exceptional Early Closure
Early Closure Does Not Create Available Money From Locked Capital

Accounts
Cash and Bank Tracked Separately
Multiple Cash/Bank Accounts Supported

Integrity
No Silent Financial Deletion
Corrections Must Be Audited
Historical Business Truth Is Preserved
Future Percentage Changes Never Alter Completed Past Deals

DOCUMENT STATUS
01 — BUSINESS RULES
Version: Final v0.4
Status: LOCKED — AUTHORITATIVE SOURCE OF TRUTH
ഈ document ആണ് subsequent architecture documents-ന്റെ business-rule foundation.
Implementation സമയത്ത്:
LOCKED rules invent/change ചെയ്യരുത്.
Later documents ഈ rules-നെ contradict ചെയ്യരുത്.
BUSINESS DECISION REQUIRED items മാത്രം confirmation കിട്ടുന്നതുവരെ implementation assumption ആകരുത്.
