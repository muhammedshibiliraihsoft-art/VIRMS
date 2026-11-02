import { Data, Batch, Expense, Issue, Sale, Job, Vehicle } from '../types';

export const effectiveExpense = (e: Expense): Expense => {
  const correction = e.corrections?.at(-1);
  return correction
    ? {
        ...e,
        amount: correction.amount,
        investor: correction.investor,
        capital: correction.capital,
      }
    : e;
};

export const remaining = (d: Data, b: Batch): number =>
  b.quantity -
  (d.issues || []).filter((x) => x.batchId === b.id).reduce((s, x) => s + x.quantity, 0);

export const margin = (d: Data, source: Data = d): number =>
  (d.issues || []).reduce((s, x) => {
    const b = (source.batches || []).find((bat) => bat.id === x.batchId);
    return s + x.quantity * (x.price - (b?.cost ?? 0));
  }, 0);

export const issueGarage = (d: Data, issue: Issue): string | undefined =>
  (d.jobs || []).find((j) => j.id === issue.jobId)?.garageId ??
  (d.batches || []).find((b) => b.id === issue.batchId)?.garageId;

export const vehicleCost = (d: Data, id: string): number => {
  const expenses = (d.expenses || [])
    .filter((e) => e.vehicleId === id)
    .reduce((s, e) => s + effectiveExpense(e).amount, 0);

  const directIssues = (d.issues || [])
    .filter((i) => i.vehicleId === id && !i.expenseId && !i.jobCostId)
    .reduce((s, i) => s + i.quantity * i.price, 0);

  const jobCosts = (d.jobs || [])
    .filter((j) => j.vehicleId === id)
    .reduce((sum, j) => sum + (j.costs ?? []).reduce((n, c) => n + c.amount, 0), 0);

  return expenses + directIssues + jobCosts;
};

export const totalVehicleCost = (d: Data, id: string): number =>
  ((d.vehicles || []).find((v) => v.id === id)?.purchase ?? 0) + vehicleCost(d, id);

export const garageVehicleCost = (
  d: Data,
  vehicleId: string,
  garageId: string
): number => {
  const expenses = (d.expenses || [])
    .filter((e) => e.vehicleId === vehicleId && e.garageId === garageId)
    .reduce((s, e) => s + effectiveExpense(e).amount, 0);

  const directIssues = (d.issues || [])
    .filter(
      (i) =>
        i.vehicleId === vehicleId &&
        !i.expenseId &&
        !i.jobCostId &&
        issueGarage(d, i) === garageId
    )
    .reduce((s, i) => s + i.quantity * i.price, 0);

  const jobCosts = (d.jobs || [])
    .filter((j) => j.vehicleId === vehicleId && j.garageId === garageId)
    .reduce((s, j) => s + (j.costs ?? []).reduce((n, c) => n + c.amount, 0), 0);

  return expenses + directIssues + jobCosts;
};

export const salePrice = (sale: Sale): number =>
  sale.corrections?.at(-1)?.price ?? sale.price;

export const paid = (
  d: Data,
  kind: 'buyer' | 'customer' | 'capital',
  id: string
): number =>
  (d.payments || [])
    .filter((p) => p.kind === kind && p.targetId === id)
    .reduce((s, p) => s + p.amount, 0);

export const buyerRefunded = (d: Data, saleId: string): number =>
  Math.round(
    (d.buyerRefunds ?? [])
      .filter((r) => r.saleId === saleId)
      .reduce((n, r) => n + r.amount, 0) * 100
  ) / 100;

export const buyerNetReceived = (d: Data, sale: Sale): number =>
  Math.max(
    0,
    Math.round(
      (sale.received + paid(d, 'buyer', sale.id) - buyerRefunded(d, sale.id)) * 100
    ) / 100
  );

export const buyerRefundPayable = (d: Data, sale: Sale): number =>
  Math.max(
    0,
    Math.round((buyerNetReceived(d, sale) - salePrice(sale)) * 100) / 100
  );

export const buyerReceivable = (d: Data, sale: Sale): number =>
  Math.max(
    0,
    Math.round((salePrice(sale) - buyerNetReceived(d, sale)) * 100) / 100
  );

export const capitalContribution = (d: Data, id: string): number => {
  const expenseCapital = (d.expenses || [])
    .filter((e) => e.vehicleId === id)
    .reduce((s, e) => s + effectiveExpense(e).capital, 0);

  const issueCapital = (d.issues || [])
    .filter((i) => i.vehicleId === id && !i.expenseId)
    .reduce((s, i) => s + (i.capital ?? 0), 0);

  return expenseCapital + issueCapital;
};

export interface CapitalReportResult {
  rows: {
    vehicleId: string;
    vehicleNumber: string;
    contribution: number;
    selectedContribution: number;
    recovery: number;
    open: number;
    incomplete: boolean;
    selectedIncomplete: boolean;
  }[];
  selectedContribution: number;
  selectedIncomplete: boolean;
  companyContribution: number;
  companyRecovery: number;
  companyOpen: number;
  incomplete: boolean;
}

export function capitalReport(data: Data, garageIds: string[]): CapitalReportResult {
  const garages = new Set(garageIds);
  const rows = (data.vehicles || [])
    .filter((v) => v.type === 'Stock / Investor')
    .map((vehicle) => {
      const expenses = (data.expenses || []).filter((e) => e.vehicleId === vehicle.id);
      const issues = (data.issues || []).filter(
        (i) => i.vehicleId === vehicle.id && !i.expenseId
      );
      const selectedExpenses = expenses.filter((e) => garages.has(e.garageId));
      const selectedIssues = issues.filter((i) => {
        const garage = issueGarage(data, i);
        return garage !== undefined && garages.has(garage);
      });
      const sum = (values: number[]) =>
        values.reduce((n, val) => n + Math.round(val * 100), 0) / 100;
      const contribution = sum([
        ...expenses.map((e) => effectiveExpense(e).capital),
        ...issues.map((i) => i.capital ?? 0),
      ]);
      const selectedContribution = sum([
        ...selectedExpenses.map((e) => effectiveExpense(e).capital),
        ...selectedIssues.map((i) => i.capital ?? 0),
      ]);
      const recovery = sum(
        (data.payments || [])
          .filter((p) => p.kind === 'capital' && p.targetId === vehicle.id)
          .map((p) => p.amount)
      );
      const incomplete = issues.some(
        (i) => i.investor === undefined || i.capital === undefined
      );
      const selectedIncomplete = selectedIssues.some(
        (i) => i.investor === undefined || i.capital === undefined
      );
      return {
        vehicleId: vehicle.id,
        vehicleNumber: vehicle.number,
        contribution,
        selectedContribution,
        recovery,
        open: (Math.round(contribution * 100) - Math.round(recovery * 100)) / 100,
        incomplete,
        selectedIncomplete,
      };
    });

  const sum = (values: number[]) =>
    values.reduce((n, val) => n + Math.round(val * 100), 0) / 100;

  return {
    rows: rows.filter((r) => r.selectedContribution > 0 || r.selectedIncomplete),
    selectedContribution: sum(rows.map((r) => r.selectedContribution)),
    selectedIncomplete: rows.some((r) => r.selectedIncomplete),
    companyContribution: sum(rows.map((r) => r.contribution)),
    companyRecovery: sum(rows.map((r) => r.recovery)),
    companyOpen: sum(rows.map((r) => r.open)),
    incomplete: rows.some((r) => r.incomplete),
  };
}

export const otherIncomeTotal = (d: Data): number =>
  (d.otherIncomeReceipts ?? []).reduce(
    (sum, r) => sum + Math.round(r.amount * 100),
    0
  ) / 100;

export const totals = (d: Data, source: Data = d) => ({
  otherIncome: otherIncomeTotal(d),
  vehicles: (d.vehicles || []).length,
  jobs: (d.jobs || []).filter((j) => j.status === 'Open').length,
  revenue: (d.jobs || []).reduce(
    (s, j) => s + j.received + paid(d, 'customer', j.id),
    0
  ),
  outstanding: (d.jobs || []).reduce(
    (s, j) => s + j.charge - j.received - paid(d, 'customer', j.id),
    0
  ),
  expenses: (d.expenses || [])
    .filter((e) => e.category === 'Company')
    .reduce((s, e) => s + effectiveExpense(e).amount, 0),
  capital: capitalReport(
    source,
    (source.garages || []).map((g) => g.id)
  ).companyOpen,
  receivable: (d.sales || []).reduce((s, x) => s + buyerReceivable(d, x), 0),
  stock: (d.batches || []).reduce(
    (s, b) => s + remaining(source, b) * b.cost,
    0
  ),
  margin: margin(d, source),
});

export interface InventoryFilter {
  garageId?: string;
  itemId?: string;
  from?: string;
  to?: string;
}

export function inventoryReport(data: Data, filter: InventoryFilter = {}) {
  const within = (date: string) =>
    (!filter.from || date >= filter.from) && (!filter.to || date <= filter.to);

  const batches = (data.batches || []).filter(
    (b) =>
      (!filter.garageId || filter.garageId === 'all' || b.garageId === filter.garageId) &&
      (!filter.itemId || b.itemId === filter.itemId) &&
      within(b.date)
  );

  const issues = (data.issues || []).filter((i) => {
    const batch = (data.batches || []).find((b) => b.id === i.batchId);
    return (
      !!batch &&
      (!filter.garageId || filter.garageId === 'all' || issueGarage(data, i) === filter.garageId) &&
      (!filter.itemId || batch.itemId === filter.itemId) &&
      within(i.date)
    );
  });

  return {
    batches,
    issues,
    purchased: batches.reduce((n, b) => n + b.quantity, 0),
    purchaseCost: batches.reduce((n, b) => n + b.quantity * b.cost, 0),
    issued: issues.reduce((n, i) => n + i.quantity, 0),
    issueValue: issues.reduce((n, i) => n + i.quantity * i.price, 0),
    costBasis: issues.reduce((n, i) => {
      const b = (data.batches || []).find((bat) => bat.id === i.batchId);
      return n + i.quantity * (b?.cost ?? 0);
    }, 0),
    remaining: batches.reduce((n, b) => n + remaining(data, b), 0),
  };
}

export interface CompanyReportValues {
  customerReceipts: number;
  otherIncome: number;
  companyExpenses: number;
  inventoryMargin: number;
  runningCapitalOpen: number;
}

export interface GarageReportValues {
  garageId: string;
  name: string;
  customerReceipts: number;
  otherIncome: number;
  companyExpenses: number;
  inventoryMargin: number;
}

export function companyReportValues(data: Data, garageId?: string): CompanyReportValues {
  const inScope = (id: string) =>
    garageId === undefined || garageId === 'all' || id === garageId;
  const scopedInventory = inventoryReport(data, {
    garageId: garageId === 'all' ? undefined : garageId,
  });
  const sum = (values: number[]) =>
    values.reduce((total, value) => total + Math.round(value * 100), 0) / 100;

  return {
    customerReceipts: sum(
      (data.jobs || [])
        .filter((j) => inScope(j.garageId))
        .map((j) => j.received + paid(data, 'customer', j.id))
    ),
    otherIncome: sum(
      (data.otherIncomeReceipts ?? [])
        .filter((r) => inScope(r.garageId))
        .map((r) => r.amount)
    ),
    companyExpenses: sum(
      (data.expenses || [])
        .filter((e) => e.category === 'Company' && inScope(e.garageId))
        .map((e) => effectiveExpense(e).amount)
    ),
    inventoryMargin:
      Math.round((scopedInventory.issueValue - scopedInventory.costBasis) * 100) / 100,
    runningCapitalOpen: capitalReport(
      data,
      (data.garages || []).map((g) => g.id)
    ).companyOpen,
  };
}

export function garageReportValues(
  data: Data,
  garageId?: string
): GarageReportValues[] {
  return (data.garages || [])
    .filter((g) => garageId === undefined || garageId === 'all' || g.id === garageId)
    .map((g) => {
      const values = companyReportValues(data, g.id);
      return {
        garageId: g.id,
        name: g.name,
        customerReceipts: values.customerReceipts,
        otherIncome: values.otherIncome,
        companyExpenses: values.companyExpenses,
        inventoryMargin: values.inventoryMargin,
      };
    });
}

export interface FundHistoryRow {
  id: string;
  date: string;
  description: string;
  credit: number;
  debit: number;
  reserved?: number;
  sourceId: string;
}

function refundReserve(data: Data, vehicleIds: Set<string>): number {
  return (data.sales || [])
    .filter((s) => vehicleIds.has(s.vehicleId))
    .reduce((sum, sale) => {
      const recovered = (data.principalRecoveries ?? [])
        .filter((r) => r.saleId === sale.id)
        .reduce((n, r) => n + Math.round(r.amount * 100), 0);
      const refunded = (data.buyerRefunds ?? [])
        .filter((r) => r.saleId === sale.id)
        .reduce((n, r) => n + Math.round(r.principalBacked * 100), 0);
      const payable = Math.max(
        0,
        Math.round(
          (sale.received +
            paid(data, 'buyer', sale.id) -
            (data.buyerRefunds ?? [])
              .filter((r) => r.saleId === sale.id)
              .reduce((n, r) => n + r.amount, 0) -
            salePrice(sale)) *
            100
        )
      );
      return sum + Math.min(Math.max(0, recovered - refunded), payable);
    }, 0);
}

export function fundHistory(data: Data, investorId: string): FundHistoryRow[] {
  const investor = (data.investors || []).find((i) => i.id === investorId);
  if (!investor) return [];

  const vehicles = (data.vehicles || []).filter((v) => v.investorId === investorId);
  const ids = new Set(vehicles.map((v) => v.id));
  const rows: FundHistoryRow[] = [
    {
      id: investor.id,
      date: '',
      description: 'Seeded opening principal',
      credit: investor.principal,
      debit: 0,
      sourceId: investor.id,
    },
  ];

  for (const credit of data.fundCredits ?? []) {
    if (credit.investorId === investorId) {
      rows.push({
        id: credit.id,
        date: credit.date,
        description: 'Additional capital',
        credit: credit.amount,
        debit: 0,
        sourceId: credit.id,
      });
    }
  }

  for (const vehicle of vehicles) {
    if (vehicle.purchase > 0) {
      rows.push({
        id: vehicle.id,
        date: '',
        description: `Vehicle purchase · ${vehicle.number}`,
        credit: 0,
        debit: vehicle.purchase,
        sourceId: vehicle.id,
      });
    }
  }

  for (const expense of data.expenses || []) {
    if (ids.has(expense.vehicleId)) {
      const current = effectiveExpense(expense);
      if (current.investor > 0) {
        rows.push({
          id: expense.id,
          date: expense.date,
          description: `Expense · ${expense.description}${
            expense.corrections?.length ? ' (corrected)' : ''
          }`,
          credit: 0,
          debit: current.investor,
          sourceId: expense.id,
        });
      }
    }
  }

  for (const issue of data.issues || []) {
    if (!issue.expenseId && ids.has(issue.vehicleId) && (issue.investor ?? 0) > 0) {
      rows.push({
        id: issue.id,
        date: issue.date,
        description: 'Inventory issue',
        credit: 0,
        debit: issue.investor ?? 0,
        sourceId: issue.id,
      });
    }
  }

  for (const recovery of data.principalRecoveries ?? []) {
    if (ids.has(recovery.vehicleId)) {
      rows.push({
        id: recovery.id,
        date: recovery.date,
        description: 'Confirmed principal recovery',
        credit: recovery.amount,
        debit: 0,
        sourceId: recovery.saleId,
      });
    }
  }

  for (const refund of data.buyerRefunds ?? []) {
    const sale = (data.sales || []).find((s) => s.id === refund.saleId);
    if (sale && ids.has(sale.vehicleId) && refund.principalBacked > 0) {
      rows.push({
        id: refund.id,
        date: refund.date,
        description: 'Principal-backed buyer refund',
        credit: 0,
        debit: refund.principalBacked,
        sourceId: refund.saleId,
      });
    }
  }

  return rows;
}

export function fundPosition(data: Data, investorId: string) {
  const investor = (data.investors || []).find((i) => i.id === investorId);
  if (!investor) {
    return { principal: 0, used: 0, available: 0, recovered: 0, reserve: 0, incomplete: false };
  }

  const vehicles = (data.vehicles || []).filter((v) => v.investorId === investorId);
  const ids = new Set(vehicles.map((v) => v.id));
  const incomplete = (data.issues || []).some(
    (i) =>
      !i.expenseId &&
      ids.has(i.vehicleId) &&
      (i.investor === undefined || i.capital === undefined)
  );

  const purchases = vehicles.reduce((s, v) => s + Math.round(v.purchase * 100), 0);
  const expenses = (data.expenses || [])
    .filter((e) => ids.has(e.vehicleId))
    .reduce((s, e) => s + Math.round(effectiveExpense(e).investor * 100), 0);
  const issues = (data.issues || [])
    .filter((i) => !i.expenseId && ids.has(i.vehicleId))
    .reduce((s, i) => s + Math.round((i.investor ?? 0) * 100), 0);
  const recovered =
    (data.principalRecoveries ?? [])
      .filter((r) => ids.has(r.vehicleId))
      .reduce((s, r) => s + Math.round(r.amount * 100), 0) -
    (data.buyerRefunds ?? [])
      .filter((r) => (data.sales || []).some((s) => s.id === r.saleId && ids.has(s.vehicleId)))
      .reduce((s, r) => s + Math.round(r.principalBacked * 100), 0);

  const used = purchases + expenses + issues - recovered;
  const principal =
    Math.round(investor.principal * 100) +
    (data.fundCredits ?? [])
      .filter((c) => c.investorId === investorId)
      .reduce((s, c) => s + Math.round(c.amount * 100), 0);
  const reserve = refundReserve(data, ids);

  return {
    principal: principal / 100,
    used: used / 100,
    available: (principal - used - reserve) / 100,
    recovered: recovered / 100,
    reserve: reserve / 100,
    incomplete,
  };
}

export function recoveryLimit(data: Data, vehicleId: string) {
  const vehicle = (data.vehicles || []).find((v) => v.id === vehicleId);
  const sale = (data.sales || []).find((s) => s.vehicleId === vehicleId);
  if (!vehicle || vehicle.type !== 'Stock / Investor' || !vehicle.investorId || !sale) {
    throw new Error('Select a funded vehicle with an existing sale.');
  }

  if (capitalContribution(data, vehicleId) > 0) {
    if (
      Math.round(
        (sale.received +
          paid(data, 'buyer', sale.id) -
          (data.buyerRefunds ?? [])
            .filter((r) => r.saleId === sale.id)
            .reduce((n, r) => n + r.amount, 0)) *
          100
      ) !== Math.round(salePrice(sale) * 100)
    ) {
      throw new Error('Mixed-funded recovery requires full buyer collection.');
    }
    if (
      Math.round(salePrice(sale) * 100) <=
      Math.round(totalVehicleCost(data, vehicleId) * 100)
    ) {
      throw new Error(
        'Mixed-funded recovery requires a positive vehicle result; loss requires manual review.'
      );
    }
  }

  const issues = (data.issues || []).filter(
    (i) => i.vehicleId === vehicleId && !i.expenseId
  );
  if (issues.some((i) => i.investor === undefined || i.capital === undefined)) {
    throw new Error('Resolve missing issue funding allocations first.');
  }

  const invested =
    Math.round(vehicle.purchase * 100) +
    (data.expenses || [])
      .filter((e) => e.vehicleId === vehicleId)
      .reduce((s, e) => s + Math.round(effectiveExpense(e).investor * 100), 0) +
    issues.reduce((s, i) => s + Math.round((i.investor ?? 0) * 100), 0);

  const recovered = (data.principalRecoveries ?? [])
    .filter((r) => r.vehicleId === vehicleId)
    .reduce((s, r) => s + Math.round(r.amount * 100), 0);

  const received = Math.round(
    (sale.received +
      paid(data, 'buyer', sale.id) -
      (data.buyerRefunds ?? [])
        .filter((r) => r.saleId === sale.id)
        .reduce((n, r) => n + r.amount, 0)) *
      100
  );

  return {
    saleId: sale.id,
    limit: Math.max(0, Math.min(invested - recovered, received - recovered)) / 100,
  };
}

export function validateRecovery(data: Data, vehicleId: string, amount: number) {
  const result = recoveryLimit(data, vehicleId);
  if (
    !Number.isFinite(amount) ||
    amount <= 0 ||
    Math.abs(amount * 100 - Math.round(amount * 100)) > 0.000001 ||
    Math.round(amount * 100) > Math.round(result.limit * 100)
  ) {
    throw new Error(
      'Recovery must be positive and no greater than received cash and outstanding investor principal.'
    );
  }
  return result;
}

export function validateCapitalRecovery(data: Data, vehicleId: string, amount: number) {
  const position = recoveryLimit(data, vehicleId);
  const vehicle = (data.vehicles || []).find((v) => v.id === vehicleId)!;
  const sale = (data.sales || []).find((s) => s.id === position.saleId)!;

  if (
    Math.round(
      (sale.received +
        paid(data, 'buyer', sale.id) -
        (data.buyerRefunds ?? [])
          .filter((r) => r.saleId === sale.id)
          .reduce((n, r) => n + r.amount, 0)) *
        100
    ) !== Math.round(salePrice(sale) * 100)
  ) {
    throw new Error('Capital recovery requires full buyer collection.');
  }

  if (
    Math.round(sale.price * 100) <=
    Math.round(totalVehicleCost(data, vehicle.id) * 100)
  ) {
    throw new Error(
      'Capital recovery requires a positive vehicle result; loss requires manual review.'
    );
  }

  if (Math.round(position.limit * 100) > 0) {
    throw new Error('Recover the outstanding investor principal first.');
  }

  const outstanding =
    Math.round(capitalContribution(data, vehicleId) * 100) -
    Math.round(paid(data, 'capital', vehicleId) * 100);

  if (
    !Number.isFinite(amount) ||
    amount <= 0 ||
    Math.abs(amount * 100 - Math.round(amount * 100)) > 0.000001 ||
    Math.round(amount * 100) > outstanding
  ) {
    throw new Error(
      'Capital recovery must be positive and no greater than the outstanding company contribution.'
    );
  }
  return { saleId: sale.id, limit: outstanding / 100 };
}

export function validateSaleCorrection(
  data: Data,
  saleId: string,
  price: number,
  reason: string
) {
  const sale = (data.sales || []).find((s) => s.id === saleId);
  const vehicle = sale && (data.vehicles || []).find((v) => v.id === sale.vehicleId);
  if (!sale || !vehicle) throw new Error('Select an existing sale.');
  if (
    vehicle.type !== 'Stock / Investor' ||
    capitalContribution(data, vehicle.id) > 0 ||
    paid(data, 'capital', vehicle.id) > 0
  ) {
    throw new Error(
      'Sale correction with mixed Company capital requires manual reconciliation.'
    );
  }
  if (
    !Number.isFinite(price) ||
    price <= 0 ||
    Math.abs(price * 100 - Math.round(price * 100)) > 0.000001 ||
    !reason.trim()
  ) {
    throw new Error('Enter a positive sale price and correction reason.');
  }
  const received = Math.round(
    (sale.received +
      paid(data, 'buyer', sale.id) -
      (data.buyerRefunds ?? [])
        .filter((r) => r.saleId === sale.id)
        .reduce((n, r) => n + r.amount, 0)) *
      100
  );
  if (Math.round(price * 100) > received + Math.round(buyerRefundPayable(data, sale) * 100)) {
    throw new Error('A correction cannot create an uncollected price increase.');
  }
  return {
    sale,
    oldPrice: salePrice(sale),
    newPrice: price,
    refundPayable: Math.max(0, (received - Math.round(price * 100)) / 100),
  };
}

export function validateBuyerRefund(data: Data, saleId: string, amount: number) {
  const sale = (data.sales || []).find((s) => s.id === saleId);
  const vehicle = sale && (data.vehicles || []).find((v) => v.id === sale.vehicleId);
  if (!sale || !vehicle) throw new Error('Select an existing sale.');
  if (
    vehicle.type !== 'Stock / Investor' ||
    capitalContribution(data, vehicle.id) > 0 ||
    paid(data, 'capital', vehicle.id) > 0
  ) {
    throw new Error('Refund with mixed Company capital requires manual reconciliation.');
  }
  const payable = Math.round(buyerRefundPayable(data, sale) * 100);
  const already = (data.buyerRefunds ?? [])
    .filter((r) => r.saleId === saleId)
    .reduce((n, r) => n + Math.round(r.amount * 100), 0);
  const recovered = (data.principalRecoveries ?? [])
    .filter((r) => r.vehicleId === vehicle.id)
    .reduce((n, r) => n + Math.round(r.amount * 100), 0);
  const returned = (data.buyerRefunds ?? [])
    .filter((r) => r.saleId === saleId)
    .reduce((n, r) => n + Math.round(r.principalBacked * 100), 0);
  const backed = Math.min(Math.round(amount * 100), Math.max(0, recovered - returned));

  if (
    !Number.isFinite(amount) ||
    amount <= 0 ||
    Math.abs(amount * 100 - Math.round(amount * 100)) > 0.000001 ||
    Math.round(amount * 100) > payable ||
    already + Math.round(amount * 100) >
      Math.round((sale.received + paid(data, 'buyer', saleId)) * 100)
  ) {
    throw new Error(
      'Refund must be positive and cannot exceed the current buyer refund payable.'
    );
  }
  const position = fundPosition(data, vehicle.investorId!);
  if (backed > Math.round(position.principal * 100)) {
    throw new Error('Investor Fund cannot support the principal-backed refund.');
  }
  return { principalBacked: backed / 100, payable: payable / 100 };
}

export interface ReportColumn {
  key: string;
  label: string;
  align?: 'left' | 'right' | 'center';
  format?: 'currency' | 'number' | 'text' | 'badge';
}

export interface ReportDefinition {
  id: string;
  name: string;
  category: string;
  description: string;
  columns: ReportColumn[];
  rows: Record<string, any>[];
  summary?: { label: string; value: string | number }[];
}

export function getReportData(
  reportKey: string,
  data: Data,
  garageFilter: string = 'all'
): ReportDefinition {
  const inScope = (id: string) => garageFilter === 'all' || id === garageFilter;
  const formatINR = (val: number) => '₹' + Math.round(val).toLocaleString('en-IN');

  switch (reportKey) {
    case 'Company Consolidated':
    case 'rep-consolidated': {
      const comp = companyReportValues(data, garageFilter);
      return {
        id: 'rep-consolidated',
        name: 'Company Consolidated',
        category: 'Financial',
        description: 'Comprehensive accounting components across all workshop activities',
        summary: [
          { label: 'Customer Receipts', value: formatINR(comp.customerReceipts) },
          { label: 'Other Income', value: formatINR(comp.otherIncome) },
          { label: 'Workshop Expenses', value: formatINR(comp.companyExpenses) },
          { label: 'Inventory Margin', value: formatINR(comp.inventoryMargin) },
          { label: 'Running Capital Open', value: formatINR(comp.runningCapitalOpen) },
        ],
        columns: [
          { key: 'component', label: 'Component' },
          { key: 'amount', label: 'Amount', align: 'right', format: 'currency' },
          { key: 'notes', label: 'Accounting Classification' },
        ],
        rows: [
          {
            component: 'Customer Job Receipts',
            amount: comp.customerReceipts,
            notes: 'Completed & in-progress customer work orders',
          },
          {
            component: 'Other Operational Income',
            amount: comp.otherIncome,
            notes: 'Scrap, parts recycling & non-job income',
          },
          {
            component: 'Company Operating Expenses',
            amount: comp.companyExpenses,
            notes: 'Workshop utilities, rent, supplies',
          },
          {
            component: 'Inventory Profit Margin',
            amount: comp.inventoryMargin,
            notes: 'Realized issue price minus batch cost basis',
          },
          {
            component: 'Running Capital (Unrecovered)',
            amount: comp.runningCapitalOpen,
            notes: 'Open company contribution to stock vehicles',
          },
        ],
      };
    }

    case 'Garage-wise':
    case 'rep-garage-wise': {
      const rows = garageReportValues(data, garageFilter).map((g) => ({
        garage: g.name,
        customerReceipts: g.customerReceipts,
        otherIncome: g.otherIncome,
        companyExpenses: g.companyExpenses,
        inventoryMargin: g.inventoryMargin,
      }));
      return {
        id: 'rep-garage-wise',
        name: 'Garage-wise Performance',
        category: 'Branch',
        description: 'Comparative financial components attributed to each active workshop branch',
        columns: [
          { key: 'garage', label: 'Garage Branch' },
          { key: 'customerReceipts', label: 'Customer Receipts', align: 'right', format: 'currency' },
          { key: 'otherIncome', label: 'Other Income', align: 'right', format: 'currency' },
          { key: 'companyExpenses', label: 'Expenses', align: 'right', format: 'currency' },
          { key: 'inventoryMargin', label: 'Parts Margin', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Vehicle Cost':
    case 'rep-vehicle-cost': {
      const rows = (data.vehicles || [])
        .filter((v) => inScope(v.garageId))
        .map((v) => {
          const directExpenses = (data.expenses || [])
            .filter((e) => e.vehicleId === v.id)
            .reduce((s, e) => s + effectiveExpense(e).amount, 0);
          const partsIssued = (data.issues || [])
            .filter((i) => i.vehicleId === v.id && !i.expenseId && !i.jobCostId)
            .reduce((s, i) => s + i.quantity * i.price, 0);
          const jobCosts = (data.jobs || [])
            .filter((j) => j.vehicleId === v.id)
            .reduce((s, j) => s + (j.costs ?? []).reduce((n, c) => n + c.amount, 0), 0);
          const total = v.purchase + directExpenses + partsIssued + jobCosts;
          return {
            number: v.number,
            model: v.model,
            type: v.type,
            purchase: v.purchase,
            directExpenses,
            partsIssued,
            jobCosts,
            totalCost: total,
          };
        });
      return {
        id: 'rep-vehicle-cost',
        name: 'Vehicle Cost Ledger',
        category: 'Vehicles',
        description: 'Detailed cost breakdown including purchase, workshop expenses, parts and jobs',
        columns: [
          { key: 'number', label: 'Vehicle Number' },
          { key: 'model', label: 'Model' },
          { key: 'type', label: 'Classification' },
          { key: 'purchase', label: 'Purchase', align: 'right', format: 'currency' },
          { key: 'directExpenses', label: 'Expenses', align: 'right', format: 'currency' },
          { key: 'partsIssued', label: 'Parts Issued', align: 'right', format: 'currency' },
          { key: 'totalCost', label: 'Total Cost', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Investor':
    case 'Investor Fund':
    case 'Investor Fund Report':
    case 'rep-investor-fund': {
      const rows = (data.investors || []).map((inv) => {
        const pos = fundPosition(data, inv.id);
        return {
          investor: inv.name,
          principal: pos.principal,
          used: pos.used,
          available: pos.available,
          recovered: pos.recovered,
          reserve: pos.reserve,
          status: pos.incomplete ? 'Pending Allocation' : 'Active',
        };
      });
      return {
        id: 'rep-investor-fund',
        name: 'Investor Fund Ledger',
        category: 'Investment',
        description: 'Investor capital deployment, reserves for buyer refunds, and net availability',
        columns: [
          { key: 'investor', label: 'Investor Name' },
          { key: 'principal', label: 'Principal', align: 'right', format: 'currency' },
          { key: 'used', label: 'Deployed / Used', align: 'right', format: 'currency' },
          { key: 'recovered', label: 'Recovered', align: 'right', format: 'currency' },
          { key: 'reserve', label: 'Refund Reserve', align: 'right', format: 'currency' },
          { key: 'available', label: 'Available', align: 'right', format: 'currency' },
          { key: 'status', label: 'Status' },
        ],
        rows,
      };
    }

    case 'Expense':
    case 'Company Expenses': {
      const rows = (data.expenses || [])
        .filter((e) => inScope(e.garageId))
        .map((e) => {
          const eff = effectiveExpense(e);
          const garageName = (data.garages || []).find((g) => g.id === e.garageId)?.name ?? 'Central';
          return {
            date: e.date,
            description: e.description,
            category: e.category,
            garage: garageName,
            amount: eff.amount,
            investor: eff.investor,
            capital: eff.capital,
          };
        });
      return {
        id: 'rep-expenses',
        name: 'Expense Register',
        category: 'Accounting',
        description: 'Complete record of vehicle and workshop operational expenses',
        columns: [
          { key: 'date', label: 'Date' },
          { key: 'description', label: 'Description' },
          { key: 'category', label: 'Category' },
          { key: 'garage', label: 'Garage' },
          { key: 'amount', label: 'Total Amount', align: 'right', format: 'currency' },
          { key: 'investor', label: 'Investor Share', align: 'right', format: 'currency' },
          { key: 'capital', label: 'Company Share', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Garage Jobs': {
      const rows = (data.jobs || [])
        .filter((j) => inScope(j.garageId))
        .map((j) => {
          const veh = (data.vehicles || []).find((v) => v.id === j.vehicleId);
          const totalReceived = j.received + paid(data, 'customer', j.id);
          const outstanding = Math.max(0, j.charge - totalReceived);
          return {
            number: j.number,
            vehicle: veh ? `${veh.model} (${veh.number})` : '—',
            description: j.description,
            charge: j.charge,
            received: totalReceived,
            outstanding,
            status: j.status,
            date: j.date,
          };
        });
      return {
        id: 'rep-jobs',
        name: 'Garage Jobs & Work Orders',
        category: 'Operations',
        description: 'Job cards, billable charges, payments received, and customer balance',
        columns: [
          { key: 'number', label: 'Job Number' },
          { key: 'vehicle', label: 'Vehicle' },
          { key: 'charge', label: 'Total Charge', align: 'right', format: 'currency' },
          { key: 'received', label: 'Received', align: 'right', format: 'currency' },
          { key: 'outstanding', label: 'Balance Due', align: 'right', format: 'currency' },
          { key: 'status', label: 'Status' },
          { key: 'date', label: 'Date' },
        ],
        rows,
      };
    }

    case 'Inventory Current Stock':
    case 'Stock Reports': {
      const rows = (data.batches || [])
        .filter((b) => inScope(b.garageId))
        .map((b) => {
          const it = (data.items || []).find((item) => item.id === b.itemId);
          const rem = remaining(data, b);
          const garageName = (data.garages || []).find((g) => g.id === b.garageId)?.name ?? 'Central';
          return {
            batchId: b.id.slice(-6),
            item: it?.name ?? 'Part',
            category: it?.category ?? 'General',
            garage: garageName,
            purchasedQty: b.quantity,
            remainingQty: rem,
            unitCost: b.cost,
            stockValue: rem * b.cost,
          };
        });
      return {
        id: 'rep-inv-stock',
        name: 'Inventory Current Stock',
        category: 'Inventory',
        description: 'Warehouse stock balance, batch costs, and remaining asset valuation',
        columns: [
          { key: 'item', label: 'Item Name' },
          { key: 'category', label: 'Category' },
          { key: 'garage', label: 'Warehouse Branch' },
          { key: 'remainingQty', label: 'Remaining Stock', align: 'right' },
          { key: 'unitCost', label: 'Unit Cost', align: 'right', format: 'currency' },
          { key: 'stockValue', label: 'Asset Value', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Inventory Purchases': {
      const rows = (data.batches || [])
        .filter((b) => inScope(b.garageId))
        .map((b) => {
          const it = (data.items || []).find((item) => item.id === b.itemId);
          const garageName = (data.garages || []).find((g) => g.id === b.garageId)?.name ?? 'Central';
          return {
            date: b.date,
            batchId: b.id.slice(-6),
            item: it?.name ?? 'Part',
            garage: garageName,
            quantity: b.quantity,
            unitCost: b.cost,
            totalCost: b.quantity * b.cost,
          };
        });
      return {
        id: 'rep-inv-purchases',
        name: 'Inventory Purchases',
        category: 'Inventory',
        description: 'Chronological log of part procurement batches',
        columns: [
          { key: 'date', label: 'Purchase Date' },
          { key: 'item', label: 'Item Name' },
          { key: 'garage', label: 'Branch' },
          { key: 'quantity', label: 'Qty', align: 'right' },
          { key: 'unitCost', label: 'Unit Cost', align: 'right', format: 'currency' },
          { key: 'totalCost', label: 'Total Invoiced', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Inventory Issues': {
      const rows = (data.issues || []).map((i) => {
        const b = (data.batches || []).find((bat) => bat.id === i.batchId);
        const it = (data.items || []).find((item) => item.id === b?.itemId);
        const veh = (data.vehicles || []).find((v) => v.id === i.vehicleId);
        const j = (data.jobs || []).find((job) => job.id === i.jobId);
        return {
          date: i.date,
          item: it?.name ?? 'Part',
          vehicle: veh?.number ?? '—',
          job: j?.number ?? '—',
          quantity: i.quantity,
          price: i.price,
          totalValue: i.quantity * i.price,
          investor: i.investor ?? 0,
          capital: i.capital ?? 0,
        };
      });
      return {
        id: 'rep-inv-issues',
        name: 'Inventory Stock Issues',
        category: 'Inventory',
        description: 'Parts dispensed to vehicles and garage work orders',
        columns: [
          { key: 'date', label: 'Date' },
          { key: 'item', label: 'Item' },
          { key: 'vehicle', label: 'Vehicle' },
          { key: 'job', label: 'Job' },
          { key: 'quantity', label: 'Qty', align: 'right' },
          { key: 'price', label: 'Unit Price', align: 'right', format: 'currency' },
          { key: 'totalValue', label: 'Billed Value', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Product Margin':
    case 'rep-product-margin': {
      const rows = (data.issues || []).map((i) => {
        const b = (data.batches || []).find((bat) => bat.id === i.batchId);
        const it = (data.items || []).find((item) => item.id === b?.itemId);
        const costBasis = i.quantity * (b?.cost ?? 0);
        const revenue = i.quantity * i.price;
        const profitMargin = revenue - costBasis;
        return {
          item: it?.name ?? 'Part',
          quantity: i.quantity,
          unitCost: b?.cost ?? 0,
          unitPrice: i.price,
          costBasis,
          revenue,
          profitMargin,
        };
      });
      return {
        id: 'rep-product-margin',
        name: 'Product Margin Analysis',
        category: 'Inventory',
        description: 'Realized gross profit and markup on inventory issued to jobs',
        columns: [
          { key: 'item', label: 'Item' },
          { key: 'quantity', label: 'Qty Issued', align: 'right' },
          { key: 'costBasis', label: 'Batch Cost Basis', align: 'right', format: 'currency' },
          { key: 'revenue', label: 'Issue Revenue', align: 'right', format: 'currency' },
          { key: 'profitMargin', label: 'Gross Margin', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Sales':
    case 'Vehicle Sales': {
      const rows = (data.sales || []).map((s) => {
        const veh = (data.vehicles || []).find((v) => v.id === s.vehicleId);
        const finalPrice = salePrice(s);
        const netRcvd = buyerNetReceived(data, s);
        const due = buyerReceivable(data, s);
        return {
          vehicle: veh ? `${veh.model} (${veh.number})` : '—',
          buyer: s.buyer,
          agreedPrice: finalPrice,
          received: netRcvd,
          receivable: due,
          status: due === 0 ? 'Fully Collected' : 'Balance Pending',
        };
      });
      return {
        id: 'rep-sales',
        name: 'Vehicle Sales Register',
        category: 'Sales',
        description: 'Sold vehicles, agreed contract prices, collections and pending balances',
        columns: [
          { key: 'vehicle', label: 'Vehicle' },
          { key: 'buyer', label: 'Buyer Name' },
          { key: 'agreedPrice', label: 'Sale Price', align: 'right', format: 'currency' },
          { key: 'received', label: 'Net Collected', align: 'right', format: 'currency' },
          { key: 'receivable', label: 'Receivable Due', align: 'right', format: 'currency' },
          { key: 'status', label: 'Collection Status' },
        ],
        rows,
      };
    }

    case 'Buyer Receivables':
    case 'rep-buyer-receivables': {
      const rows = (data.sales || [])
        .map((s) => {
          const veh = (data.vehicles || []).find((v) => v.id === s.vehicleId);
          const finalPrice = salePrice(s);
          const netRcvd = buyerNetReceived(data, s);
          const due = buyerReceivable(data, s);
          return {
            vehicle: veh?.number ?? '—',
            buyer: s.buyer,
            price: finalPrice,
            collected: netRcvd,
            outstandingDue: due,
          };
        })
        .filter((r) => r.outstandingDue > 0);
      return {
        id: 'rep-buyer-receivables',
        name: 'Buyer Receivables Aging',
        category: 'Sales',
        description: 'Uncollected buyer balances on contracted vehicle sales',
        columns: [
          { key: 'vehicle', label: 'Vehicle Number' },
          { key: 'buyer', label: 'Buyer Name' },
          { key: 'price', label: 'Agreed Price', align: 'right', format: 'currency' },
          { key: 'collected', label: 'Collected to Date', align: 'right', format: 'currency' },
          { key: 'outstandingDue', label: 'Outstanding Balance', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Customer Garage Receivables': {
      const rows = (data.jobs || [])
        .filter((j) => inScope(j.garageId))
        .map((j) => {
          const veh = (data.vehicles || []).find((v) => v.id === j.vehicleId);
          const totalReceived = j.received + paid(data, 'customer', j.id);
          const due = Math.max(0, j.charge - totalReceived);
          return {
            jobNumber: j.number,
            vehicle: veh?.number ?? '—',
            customer: veh?.person ?? 'Customer',
            charge: j.charge,
            received: totalReceived,
            due,
          };
        })
        .filter((r) => r.due > 0);
      return {
        id: 'rep-customer-receivables',
        name: 'Customer Garage Receivables',
        category: 'Operations',
        description: 'Unpaid customer balances on service and repair work orders',
        columns: [
          { key: 'jobNumber', label: 'Job Number' },
          { key: 'vehicle', label: 'Vehicle Number' },
          { key: 'customer', label: 'Customer Name' },
          { key: 'charge', label: 'Job Charge', align: 'right', format: 'currency' },
          { key: 'received', label: 'Paid', align: 'right', format: 'currency' },
          { key: 'due', label: 'Uncollected', align: 'right', format: 'currency' },
        ],
        rows,
      };
    }

    case 'Running Capital': {
      const cap = capitalReport(
        data,
        (data.garages || []).map((g) => g.id)
      );
      return {
        id: 'rep-running-capital',
        name: 'Company Running Capital',
        category: 'Accounting',
        description: 'Vehicle-linked company capital investments and recoveries',
        summary: [
          { label: 'Total Contribution', value: formatINR(cap.companyContribution) },
          { label: 'Total Recovered', value: formatINR(cap.companyRecovery) },
          { label: 'Net Open Capital', value: formatINR(cap.companyOpen) },
        ],
        columns: [
          { key: 'vehicleNumber', label: 'Vehicle Number' },
          { key: 'contribution', label: 'Company Investment', align: 'right', format: 'currency' },
          { key: 'recovery', label: 'Recovered', align: 'right', format: 'currency' },
          { key: 'open', label: 'Open Contribution', align: 'right', format: 'currency' },
        ],
        rows: cap.rows,
      };
    }

    case 'Company Result': {
      const comp = companyReportValues(data, garageFilter);
      const netCash = comp.customerReceipts + comp.otherIncome - comp.companyExpenses;
      return {
        id: 'rep-company-result',
        name: 'Company Operational Result',
        category: 'Financial',
        description: 'Attributed revenues, workshop expenses, and operational margin components',
        summary: [
          { label: 'Operational Revenue', value: formatINR(comp.customerReceipts + comp.otherIncome) },
          { label: 'Operational Expenses', value: formatINR(comp.companyExpenses) },
          { label: 'Net Operating Flow', value: formatINR(netCash) },
        ],
        columns: [
          { key: 'metric', label: 'Operational Metric' },
          { key: 'value', label: 'Value', align: 'right', format: 'currency' },
          { key: 'status', label: 'Status' },
        ],
        rows: [
          { metric: 'Customer Work Order Receipts', value: comp.customerReceipts, status: 'Verified Cash' },
          { metric: 'Scrap & Other Receipts', value: comp.otherIncome, status: 'Verified Cash' },
          { metric: 'Workshop Operating Overhead', value: comp.companyExpenses, status: 'Recorded Outflow' },
          { metric: 'Realized Parts Margin', value: comp.inventoryMargin, status: 'Gross Contribution' },
        ],
      };
    }

    case 'Owner Distribution': {
      return {
        id: 'rep-owner-dist',
        name: 'Owner Distribution (Read-only notice)',
        category: 'Governance',
        description: 'Owner profit drawing formulas require business decision approval',
        columns: [
          { key: 'clause', label: 'Governing Clause' },
          { key: 'status', label: 'Status' },
          { key: 'notes', label: 'Governance Detail' },
        ],
        rows: [
          {
            clause: 'BDR-08 Owner Distribution',
            status: 'BUSINESS DECISION REQUIRED',
            notes: 'Drawing policies are unapproved in V2. No automated distributions are calculated.',
          },
        ],
      };
    }

    default: {
      return {
        id: 'rep-default',
        name: reportKey,
        category: 'Standard',
        description: `Operational report for ${reportKey}`,
        columns: [
          { key: 'id', label: 'ID' },
          { key: 'name', label: 'Name' },
          { key: 'status', label: 'Status' },
        ],
        rows: [
          { id: '1', name: reportKey, status: 'Active' },
        ],
      };
    }
  }
}
