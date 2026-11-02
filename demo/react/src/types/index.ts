export interface Garage {
  id: string;
  name: string;
  location: string;
  active: boolean;
}

export interface Investor {
  id: string;
  name: string;
  principal: number;
  used?: number;
  available?: number;
}

export interface FundCredit {
  id: string;
  investorId: string;
  amount: number;
  date: string;
  note: string;
}

export interface PrincipalRecovery {
  id: string;
  vehicleId: string;
  saleId: string;
  amount: number;
  date: string;
}

export type VehicleStatus =
  | 'In work'
  | 'Sold'
  | 'In service'
  | 'Completed'
  | 'Purchased'
  | 'Customer Vehicle';

export interface Vehicle {
  id: string;
  number: string;
  model: string;
  type: 'Stock / Investor' | 'Customer';
  garageId: string;
  person: string;
  investorId?: string;
  status: VehicleStatus;
  purchase: number;
  totalCost?: number;
  imageUrl?: string | null;
}

export interface WorkEntry {
  id: string;
  date: string;
  category: 'Work' | 'Labour' | string;
  description: string;
}

export interface JobCost {
  id: string;
  date: string;
  category: 'Labour' | 'Direct purchase' | 'Other' | string;
  description: string;
  amount: number;
}

export interface JobCharge {
  id: string;
  date: string;
  category: 'Work' | 'Labour' | 'Material' | 'Other' | string;
  description: string;
  amount: number;
}

export interface StatusHistoryEntry {
  id: string;
  timestamp: string;
  from: string;
  to: string;
  actor: string;
  note: string;
}

export interface Job {
  id: string;
  vehicleId: string;
  garageId: string;
  number: string;
  description: string;
  status: 'Open' | 'Completed';
  date: string;
  charge: number;
  received: number;
  workEntries?: WorkEntry[];
  costs?: JobCost[];
  charges?: JobCharge[];
  statusHistory?: StatusHistoryEntry[];
}

export interface Item {
  id: string;
  name: string;
  category: string;
  active: boolean;
}

export interface Batch {
  id: string;
  itemId: string;
  garageId: string;
  date: string;
  quantity: number;
  cost: number;
}

export interface Issue {
  id: string;
  batchId: string;
  vehicleId: string;
  jobId: string;
  expenseId?: string;
  jobCostId?: string;
  quantity: number;
  price: number;
  date: string;
  investor?: number;
  capital?: number;
}

export interface ExpenseCorrection {
  id: string;
  date: string;
  reason: string;
  oldAmount: number;
  oldInvestor: number;
  oldCapital: number;
  amount: number;
  investor: number;
  capital: number;
}

export interface Expense {
  id: string;
  vehicleId: string;
  garageId: string;
  description: string;
  amount: number;
  investor: number;
  capital: number;
  date: string;
  category: 'Vehicle' | 'Company';
  jobId?: string;
  costType?: 'Labour' | 'Direct purchase' | 'Other';
  corrections?: ExpenseCorrection[];
}

export interface SaleCorrection {
  id: string;
  date: string;
  actor: string;
  reason: string;
  oldPrice: number;
  price: number;
}

export interface Sale {
  id: string;
  vehicleId: string;
  buyer: string;
  price: number;
  received: number;
  corrections?: SaleCorrection[];
}

export interface BuyerRefund {
  id: string;
  saleId: string;
  amount: number;
  principalBacked: number;
  date: string;
  method: string;
  reason: string;
}

export interface AuditRecord {
  id: string;
  date: string;
  action: string;
  detail: string;
}

export interface Payment {
  id: string;
  kind: 'buyer' | 'customer' | 'capital';
  targetId: string;
  amount: number;
  date: string;
  method: string;
}

export interface OtherIncomeReceipt {
  id: string;
  garageId: string;
  description: string;
  source: string;
  amount: number;
  method: 'Cash' | 'Bank transfer' | 'UPI' | string;
  timestamp: string;
  actor: string;
}

export interface ActivityItem {
  id: string;
  code: string;
  title: string;
  subtitle: string;
  amount: number;
  status: string;
  statusVariant: 'success' | 'warning' | 'info' | 'neutral';
  date: string;
  type: 'vehicle' | 'job' | 'sale' | 'purchase';
}

export interface Data {
  garages: Garage[];
  investors: Investor[];
  vehicles: Vehicle[];
  jobs: Job[];
  items: Item[];
  batches: Batch[];
  issues: Issue[];
  expenses: Expense[];
  sales: Sale[];
  payments: Payment[];
  audit: AuditRecord[];
  buyerRefunds?: BuyerRefund[];
  fundCredits?: FundCredit[];
  principalRecoveries?: PrincipalRecovery[];
  otherIncomeReceipts?: OtherIncomeReceipt[];
}
