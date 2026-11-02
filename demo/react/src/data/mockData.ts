import {
  Garage,
  Investor,
  Vehicle,
  Job,
  Item,
  Batch,
  Issue,
  Expense,
  Sale,
  Payment,
  AuditRecord,
  FundCredit,
  PrincipalRecovery,
  BuyerRefund,
  OtherIncomeReceipt,
  ActivityItem,
  Data,
} from '../types';

export const initialGarages: Garage[] = [
  { id: 'g-1', name: 'Central Garage', location: 'Kozhikode', active: true },
  { id: 'g-2', name: 'West Garage', location: 'Malappuram', active: true },
];

export const initialInvestors: Investor[] = [
  { id: 'inv-1', name: 'Ayaan Rahman', principal: 2400000, used: 1453300, available: 946700 },
  { id: 'inv-2', name: 'Sara Nair', principal: 900000, used: 520000, available: 380000 },
  { id: 'inv-3', name: 'Farhan Ali', principal: 600000, used: 0, available: 600000 },
  { id: 'inv-4', name: 'Low Fund Test', principal: 1000, used: 0, available: 1000 },
];

export const initialVehicles: Vehicle[] = [
  { id: 'v-6', number: 'kl10aj1234', model: 'v2', type: 'Stock / Investor', garageId: 'g-1', person: 'shibilltest', investorId: 'inv-3', status: 'Purchased', purchase: 200000, totalCost: 200000, imageUrl: null },
  { id: 'v-7', number: 'kl10aj1234', model: 'v9', type: 'Stock / Investor', garageId: 'g-2', person: 'shibilltest', investorId: 'inv-3', status: 'Purchased', purchase: 67777, totalCost: 67777 },
  { id: 'v-8', number: 'kl10aj1234', model: 'v2', type: 'Customer', garageId: 'g-1', person: 'shibilltest', status: 'Customer Vehicle', purchase: 0, totalCost: 0 },
  { id: 'v-1', number: 'KL 11 AB 4821', model: 'Jeep Wrangler Rubicon', type: 'Stock / Investor', garageId: 'g-1', person: 'Ayaan Rahman', investorId: 'inv-1', status: 'In work', purchase: 780000, totalCost: 815300, imageUrl: '/vehicles/jeep-rubicon.png' },
  { id: 'v-2', number: 'KL 10 CK 2098', model: 'Jeep Compass Limited', type: 'Stock / Investor', garageId: 'g-2', person: 'Sara Nair', investorId: 'inv-2', status: 'Sold', purchase: 520000, totalCost: 520000 },
  { id: 'v-3', number: 'KL 11 DR 6412', model: 'Jeep Grand Cherokee', type: 'Customer', garageId: 'g-1', person: 'Nihal Menon', status: 'In service', purchase: 0, totalCost: 0 },
  { id: 'v-4', number: 'KL 55 P 7362', model: 'Jeep Meridian Limited', type: 'Customer', garageId: 'g-2', person: 'Maya Joseph', status: 'Completed', purchase: 0, totalCost: 0 },
  { id: 'v-5', number: 'KL 07 BW 3410', model: 'Jeep Gladiator', type: 'Stock / Investor', garageId: 'g-1', person: 'Ayaan Rahman', investorId: 'inv-1', status: 'Sold', purchase: 650000, totalCost: 650000 },
];

export const initialJobs: Job[] = [
  {
    id: 'j-1048',
    vehicleId: 'v-8',
    garageId: 'g-1',
    number: 'JOB-1048',
    description: 'Kodakasseri Irshadul Ummah Sangham – Mathruka Mahallu Samithi',
    status: 'Open',
    date: '2026-10-29',
    charge: 1000,
    received: 0,
    workEntries: [
      {
        id: 'we-1',
        date: '2026-10-29',
        category: 'Work',
        description: 'Kodakasseri Irshadul Ummah Sangham – Mathruka Mahallu Samithi',
      },
    ],
    costs: [],
    charges: [
      {
        id: 'jc-1',
        date: '2026-10-29',
        category: 'Work',
        description: 'Service & diagnostic labor',
        amount: 1000,
      },
    ],
    statusHistory: [
      {
        id: 'sh-1',
        timestamp: '2026-10-29 10:15',
        from: 'Draft',
        to: 'Open',
        actor: 'Demo Accountant',
        note: 'Job initiated in demo session',
      },
    ],
  },
  {
    id: 'j-1047',
    vehicleId: 'v-4',
    garageId: 'g-2',
    number: 'JOB-1047',
    description: 'TEST',
    status: 'Open',
    date: '2026-10-28',
    charge: 0,
    received: 0,
    workEntries: [],
    costs: [],
    charges: [],
    statusHistory: [],
  },
  {
    id: 'j-1',
    vehicleId: 'v-1',
    garageId: 'g-1',
    number: 'JOB-1042',
    description: 'Body restoration & repaint',
    status: 'Open',
    date: '2026-10-20',
    charge: 0,
    received: 0,
    workEntries: [
      {
        id: 'we-2',
        date: '2026-10-20',
        category: 'Body Work',
        description: 'Quarter panel dent removal and surface prep',
      },
      {
        id: 'we-3',
        date: '2026-10-21',
        category: 'Paint',
        description: 'Multi-coat ceramic finish primer application',
      },
    ],
    costs: [
      {
        id: 'cost-1',
        date: '2026-10-21',
        category: 'Labour',
        description: 'Body restoration specialist labor',
        amount: 32000,
      },
    ],
    charges: [],
    statusHistory: [
      {
        id: 'sh-2',
        timestamp: '2026-10-20 09:30',
        from: 'Draft',
        to: 'Open',
        actor: 'Central Garage Manager',
        note: 'Initial body inspection completed',
      },
    ],
  },
  {
    id: 'j-2',
    vehicleId: 'v-3',
    garageId: 'g-1',
    number: 'JOB-1043',
    description: 'Periodic service and brakes',
    status: 'Open',
    date: '2026-10-23',
    charge: 18500,
    received: 10000,
    workEntries: [
      {
        id: 'we-4',
        date: '2026-10-23',
        category: 'Inspection',
        description: 'Brake fluid check & pad wear analysis',
      },
    ],
    costs: [],
    charges: [
      {
        id: 'jc-2',
        date: '2026-10-23',
        category: 'Labour',
        description: 'Brake pad installation & calibration',
        amount: 8500,
      },
      {
        id: 'jc-3',
        date: '2026-10-23',
        category: 'Work',
        description: 'Full synthetic oil replacement',
        amount: 10000,
      },
    ],
    statusHistory: [
      {
        id: 'sh-3',
        timestamp: '2026-10-23 11:00',
        from: 'Draft',
        to: 'Open',
        actor: 'Central Garage Technician',
        note: 'Vehicle accepted into active bay',
      },
    ],
  },
  {
    id: 'j-3',
    vehicleId: 'v-4',
    garageId: 'g-2',
    number: 'JOB-1036',
    description: 'Suspension overhaul',
    status: 'Completed',
    date: '2026-10-10',
    charge: 24000,
    received: 24000,
    workEntries: [
      {
        id: 'we-5',
        date: '2026-10-10',
        category: 'Mechanical',
        description: 'Strut replacement and link rod adjustment',
      },
    ],
    costs: [],
    charges: [
      {
        id: 'jc-4',
        date: '2026-10-10',
        category: 'Labour',
        description: 'Front & rear suspension assembly overhaul',
        amount: 24000,
      },
    ],
    statusHistory: [
      {
        id: 'sh-4',
        timestamp: '2026-10-10 17:00',
        from: 'Open',
        to: 'Completed',
        actor: 'West Garage Supervisor',
        note: 'Road test completed successfully',
      },
    ],
  },
];

export const initialItems: Item[] = [
  { id: 'it-1', name: 'Brake pad set', category: 'Brakes', active: true },
  { id: 'it-2', name: 'Engine oil 5W-30', category: 'Fluids', active: true },
  { id: 'it-3', name: 'Paint primer', category: 'Body work', active: true },
];

export const initialBatches: Batch[] = [
  { id: 'b-1', itemId: 'it-1', garageId: 'g-1', date: '2026-09-12', quantity: 20, cost: 1200 },
  { id: 'b-2', itemId: 'it-1', garageId: 'g-2', date: '2026-10-03', quantity: 12, cost: 1350 },
  { id: 'b-3', itemId: 'it-2', garageId: 'g-1', date: '2026-10-04', quantity: 40, cost: 550 },
  { id: 'b-4', itemId: 'it-3', garageId: 'g-1', date: '2026-10-05', quantity: 15, cost: 800 },
];

export const initialIssues: Issue[] = [
  { id: 'iss-1', batchId: 'b-1', vehicleId: 'v-3', jobId: 'j-2', quantity: 2, price: 1800, date: '2026-10-23' },
  { id: 'iss-2', batchId: 'b-4', vehicleId: 'v-1', jobId: 'j-1', quantity: 3, price: 1100, date: '2026-10-22', investor: 3300, capital: 0 },
];

export const initialExpenses: Expense[] = [
  {
    id: 'exp-1',
    vehicleId: 'v-1',
    garageId: 'g-1',
    description: 'Body repair labour',
    amount: 32000,
    investor: 20000,
    capital: 12000,
    date: '2026-10-21',
    category: 'Vehicle',
    jobId: 'j-1',
    costType: 'Labour',
  },
  {
    id: 'exp-2',
    vehicleId: '',
    garageId: 'g-1',
    description: 'Workshop electricity',
    amount: 8500,
    investor: 0,
    capital: 0,
    date: '2026-10-19',
    category: 'Company',
  },
  {
    id: 'exp-3',
    vehicleId: '',
    garageId: 'g-2',
    description: 'Office supplies',
    amount: 4200,
    investor: 0,
    capital: 0,
    date: '2026-10-18',
    category: 'Company',
  },
];

export const initialSales: Sale[] = [
  { id: 's-1', vehicleId: 'v-2', buyer: 'Rohan Das', price: 645000, received: 400000 },
  { id: 's-2', vehicleId: 'v-5', buyer: 'Ananya Thomas', price: 790000, received: 790000 },
];

export const initialPayments: Payment[] = [
  { id: 'pay-1', kind: 'customer', targetId: 'j-2', amount: 10000, date: '2026-10-23', method: 'UPI' },
  { id: 'pay-2', kind: 'customer', targetId: 'j-3', amount: 24000, date: '2026-10-10', method: 'Bank transfer' },
  { id: 'pay-3', kind: 'buyer', targetId: 's-1', amount: 400000, date: '2026-10-12', method: 'Bank transfer' },
  { id: 'pay-4', kind: 'buyer', targetId: 's-2', amount: 790000, date: '2026-10-05', method: 'Bank transfer' },
];

export const initialAudit: AuditRecord[] = [
  { id: 'aud-1', date: '2026-10-29', action: 'System check', detail: 'V2 demo prototype session started' },
  { id: 'aud-2', date: '2026-10-23', action: 'Customer payment recorded', detail: 'JOB-1043 · ₹10,000 received via UPI' },
  { id: 'aud-3', date: '2026-10-22', action: 'Inventory issue', detail: 'Paint primer x3 issued to JOB-1042' },
  { id: 'aud-4', date: '2026-10-21', action: 'Vehicle expense added', detail: 'Body repair labour · ₹32,000 (Investor: ₹20,000, Capital: ₹12,000)' },
  { id: 'aud-5', date: '2026-10-12', action: 'Vehicle sale collection', detail: 'Jeep Compass Limited · ₹400,000 received from Rohan Das' },
];

export const initialBuyerRefunds: BuyerRefund[] = [];
export const initialFundCredits: FundCredit[] = [];
export const initialPrincipalRecoveries: PrincipalRecovery[] = [];
export const initialOtherIncomeReceipts: OtherIncomeReceipt[] = [
  {
    id: 'inc-1',
    garageId: 'g-1',
    description: 'Scrap metal and battery recycling',
    source: 'EcoRecycle Ltd',
    amount: 14500,
    method: 'Bank transfer',
    timestamp: '2026-10-15 14:00',
    actor: 'Central Accountant',
  },
];

export const initialActivities: ActivityItem[] = [
  {
    id: 'act-1',
    code: 'KL 11 AB 4821',
    title: 'Jeep Wrangler Rubicon',
    subtitle: 'Stock / Investor · Ayaan Rahman',
    amount: 780000,
    status: 'In work',
    statusVariant: 'warning',
    date: '20 Oct, 2026 11:30 AM',
    type: 'vehicle',
  },
  {
    id: 'act-2',
    code: 'JOB-1043',
    title: 'Periodic service & brakes',
    subtitle: 'Jeep Grand Cherokee · Nihal Menon',
    amount: 18500,
    status: 'In service',
    statusVariant: 'info',
    date: '23 Oct, 2026 02:15 PM',
    type: 'job',
  },
  {
    id: 'act-3',
    code: 'INV-6002678',
    title: 'Vehicle Sale — Rohan Das',
    subtitle: 'Jeep Compass Limited · Partial Collection',
    amount: 645000,
    status: 'Completed',
    statusVariant: 'success',
    date: '12 Oct, 2026 03:45 PM',
    type: 'sale',
  },
  {
    id: 'act-4',
    code: 'JOB-1036',
    title: 'Suspension overhaul',
    subtitle: 'Jeep Meridian Limited · Maya Joseph',
    amount: 24000,
    status: 'Completed',
    statusVariant: 'success',
    date: '10 Oct, 2026 09:20 AM',
    type: 'job',
  },
  {
    id: 'act-5',
    code: 'KL 07 BW 3410',
    title: 'Jeep Gladiator',
    subtitle: 'Stock / Investor · Settled Full Sale',
    amount: 790000,
    status: 'Sold',
    statusVariant: 'neutral',
    date: '05 Oct, 2026 04:10 PM',
    type: 'vehicle',
  },
];

export const initialData: Data = {
  garages: initialGarages,
  investors: initialInvestors,
  vehicles: initialVehicles,
  jobs: initialJobs,
  items: initialItems,
  batches: initialBatches,
  issues: initialIssues,
  expenses: initialExpenses,
  sales: initialSales,
  payments: initialPayments,
  audit: initialAudit,
  buyerRefunds: initialBuyerRefunds,
  fundCredits: initialFundCredits,
  principalRecoveries: initialPrincipalRecoveries,
  otherIncomeReceipts: initialOtherIncomeReceipts,
};

export const monthlyPerformanceData = [
  { month: 'Jan', revenue: 28000, expense: 16000 },
  { month: 'Feb', revenue: 22000, expense: 12500 },
  { month: 'Mar', revenue: 11000, expense: 8000 },
  { month: 'Apr', revenue: 10500, expense: 10000 },
  { month: 'May', revenue: 6000, expense: 5000 },
  { month: 'Jun', revenue: 3500, expense: 3000 },
  { month: 'Jul', revenue: 1500, expense: 1000 },
  { month: 'Aug', revenue: 800, expense: 600 },
];
