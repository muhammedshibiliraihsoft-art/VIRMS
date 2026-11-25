import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AccountingEventRow, AccountingEventType } from '../../../api/accountingApi';
import { queryKeys } from '../../../api/queryKeys';
import { CompanyAccountingView } from '../CompanyAccountingView';

const ids = {
  user: '11111111-1111-4111-8111-111111111111',
  company: '22222222-2222-4222-8222-222222222222',
  branch: '33333333-3333-4333-8333-333333333333',
  income: '44444444-4444-4444-8444-444444444444',
  expense: '55555555-5555-4555-8555-555555555555',
  cash: '66666666-6666-4666-8666-666666666666',
  bank: '77777777-7777-4777-8777-777777777777',
  incomeCategory: '88888888-8888-4888-8888-888888888888',
  expenseCategory: '99999999-9999-4999-8999-999999999999',
};

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCompanyModuleStates: vi.fn(),
  useAccountingAccounts: vi.fn(),
  useAccountingBranches: vi.fn(),
  useAccountingCategories: vi.fn(),
  useAccountingEvent: vi.fn(),
  useAccountingEvents: vi.fn(),
  useAccountingResult: vi.fn(),
  accountingMutation: vi.fn(),
}));

vi.mock('../../../auth/AuthContext', () => ({ useAuth: mocks.useAuth }));
vi.mock('../../../api/queries', () => ({ useCompanyModuleStates: mocks.useCompanyModuleStates }));
vi.mock('../../../api/accountingQueries', () => ({
  useAccountingAccounts: mocks.useAccountingAccounts,
  useAccountingBranches: mocks.useAccountingBranches,
  useAccountingCategories: mocks.useAccountingCategories,
  useAccountingEvent: mocks.useAccountingEvent,
  useAccountingEvents: mocks.useAccountingEvents,
  useAccountingResult: mocks.useAccountingResult,
}));
vi.mock('../../../api/accountingApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../api/accountingApi')>();
  return { ...actual, accountingMutation: mocks.accountingMutation };
});

function eventRow(type: AccountingEventType): AccountingEventRow {
  const rowIds: Partial<Record<AccountingEventType, string>> = {
    INCOME: ids.income,
    EXPENSE: ids.expense,
    RECEIPT: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    PAYMENT: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    OPENING_BALANCE: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    TRANSFER: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
  };
  const rowId = rowIds[type] ?? 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee';
  return {
    id: rowId,
    company_id: ids.company,
    branch_id: ids.branch,
    branch_name: 'Main Branch',
    event_type: type,
    amount: '100.00',
    currency: 'INR' as const,
    category_id: type === 'INCOME' ? ids.incomeCategory : type === 'EXPENSE' ? ids.expenseCategory : null,
    category_name: type === 'INCOME' ? 'Service Income' : type === 'EXPENSE' ? 'Workshop Expense' : null,
    description: type === 'INCOME' ? 'Service work' : type === 'EXPENSE' ? 'Parts purchase' : `${type} event`,
    source_reference: `${type}-100`,
    effective_at: '2026-11-03T08:00:00Z',
    recorded_at: '2026-11-03T08:01:00Z',
    actor_id: ids.user,
    effect_sign: 1 as const,
    reversal_of_id: null,
    replaces_event_id: null,
  };
}

const incomeRow = eventRow('INCOME');
const expenseRow = eventRow('EXPENSE');

function eventDetail(row: AccountingEventRow) {
  return {
    ...row,
    movements: [],
    applications: [],
    reversal_event_ids: [],
    replacement_event_ids: [],
    outstanding_amount: '100.00',
  };
}

function renderView(routeKey = 'Company Income') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  const invalidate = vi.spyOn(queryClient, 'invalidateQueries');
  const onSuccess = vi.fn();
  render(
    <QueryClientProvider client={queryClient}>
      <CompanyAccountingView routeKey={routeKey} onSuccess={onSuccess} />
    </QueryClientProvider>,
  );
  return { queryClient, invalidate, onSuccess };
}

async function openTools(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Accounting tools' }));
}

async function fillIncomeOrExpense(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Amount (₹)'), '125.50');
  await user.selectOptions(screen.getByLabelText('Company category'), ids.incomeCategory);
  await user.selectOptions(screen.getByLabelText('Branch'), ids.branch);
  await user.type(screen.getByLabelText('Description'), 'Verified source record');
  await user.type(screen.getByLabelText('Source / reference'), 'SRC-125');
}

async function openCurrentEvent(user: ReturnType<typeof userEvent.setup>, row: typeof incomeRow | typeof expenseRow) {
  await user.click(screen.getByRole('row', { name: `Open ${row.event_type} record ${row.source_reference}` }));
  await user.click(await screen.findByRole('button', { name: row.event_type === 'INCOME' ? 'Record Receipt' : 'Record Payment' }));
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.useAuth.mockReturnValue({
    user: { id: ids.user },
    currentCompany: {
      id: ids.company,
      roles: ['accountant'],
      company_wide_roles: ['accountant'],
    },
  });
  mocks.useCompanyModuleStates.mockReturnValue({
    data: { modules: [{ code: 'accounting', state: 'enabled' }] },
    isSuccess: true,
    isError: false,
  });
  mocks.useAccountingBranches.mockReturnValue({
    data: [{ id: ids.branch, tenant_id: ids.company, name: 'Main Branch' }],
    isError: false,
  });
  mocks.useAccountingAccounts.mockReturnValue({
    data: [
      { id: ids.cash, account_type: 'CASH', label: 'Till', is_active: true, has_history: false, current_balance: '0.00' },
      { id: ids.bank, account_type: 'BANK', label: 'Main Bank', is_active: true, has_history: false, current_balance: '0.00' },
    ],
    isError: false,
  });
  mocks.useAccountingCategories.mockReturnValue({
    data: [
      { id: ids.incomeCategory, kind: 'INCOME', label: 'Service Income', is_active: true },
      { id: ids.expenseCategory, kind: 'EXPENSE', label: 'Workshop Expense', is_active: true },
    ],
    isError: false,
  });
  mocks.useAccountingEvents.mockImplementation((options: { eventType?: string }) => {
    const rows = options.eventType === 'EXPENSE' ? [expenseRow] : [incomeRow];
    return { data: { count: rows.length, next: null, previous: null, results: rows }, isPending: false, isError: false };
  });
  mocks.useAccountingEvent.mockImplementation((eventId: string | null) => {
    const detail = eventId === ids.expense ? eventDetail(expenseRow) : eventDetail(incomeRow);
    return { data: eventId ? detail : undefined, isPending: false, isError: false };
  });
  mocks.useAccountingResult.mockReturnValue({ isPending: true, isError: false });
  mocks.accountingMutation.mockResolvedValue({ id: ids.income });
});

describe('CompanyAccountingView backend mutations', () => {
  it('uses selected-period Accounting summary values for the Income KPI row', () => {
    mocks.useAccountingResult.mockReturnValue({
      data: {
        period: 'annual', year: 2026, month: null, branch_id: null,
        period_start: '2026-01-01', period_end: '2027-01-01', timezone: 'Asia/Kolkata',
        starts_at: '2026-01-01T00:00:00Z', ends_before: '2027-01-01T00:00:00Z',
        income_amount: '125.50', expense_amount: '25.25', accounting_result_amount: '100.25',
        income_event_count: 3, expense_event_count: 1, actual_receipts_amount: '50.00', actual_payments_amount: '5.00',
        transaction_event_count: 2, cash_inflow_amount: '50.00', cash_outflow_amount: '5.00', net_movement_amount: '45.00',
        corrected_event_count: 0, reversal_event_count: 0, reallocation_event_count: 0,
        source_version: 'a'.repeat(64), currency: 'INR', scope: 'recorded_accounting_events',
      },
      isPending: false, isError: false, isSuccess: true,
    });
    renderView('Company Income');
    expect(screen.getByLabelText('Recognized Income: ₹125.50')).toBeInTheDocument();
    expect(screen.getByLabelText('Income Events: 3')).toBeInTheDocument();
    expect(screen.getByLabelText('Actual Receipts: ₹50.00')).toBeInTheDocument();
  });

  it.each(['GARAGE_RECEIPT', 'GARAGE_COST_PAYMENT', 'LABOUR_PAYMENT'] as const)('filters Accounting tools by %s', async (type) => {
    const user = userEvent.setup();
    renderView('Accounting');
    await openTools(user);
    await user.selectOptions(screen.getByLabelText('Event type filter'), type);
    expect(mocks.useAccountingEvents).toHaveBeenCalledWith(expect.objectContaining({ eventType: type }));
  });
  it.each([
    ['Add account', 'Account type'],
    ['Add category', 'Category type'],
  ] as const)('%s initializes its fields without uncontrolled-to-controlled warnings', async (button, selectLabel) => {
    const user = userEvent.setup();
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    try {
      renderView('Accounting');
      await openTools(user);
      await user.click(screen.getByRole('button', { name: button }));
      await user.selectOptions(screen.getByLabelText(selectLabel), selectLabel === 'Account type' ? 'BANK' : 'EXPENSE');
      await user.type(screen.getByLabelText('Name'), 'New record');

      expect(consoleError.mock.calls.flat().join(' ')).not.toContain('uncontrolled input to be controlled');
    } finally {
      consoleError.mockRestore();
    }
  });

  it.each([
    ['Company Income', 'Record Income', 'incomes/', ids.incomeCategory],
    ['Company Expenses', 'Record Expense', 'expenses/', ids.expenseCategory],
  ] as const)('posts %s to its backend resource and refreshes shared queries', async (routeKey, action, path, categoryId) => {
    const user = userEvent.setup();
    const { invalidate, onSuccess } = renderView(routeKey);

    await user.click(screen.getByRole('button', { name: action }));
    await user.type(screen.getByLabelText('Amount (₹)'), '125.50');
    await user.selectOptions(screen.getByLabelText('Company category'), categoryId);
    await user.selectOptions(screen.getByLabelText('Branch'), ids.branch);
    await user.type(screen.getByLabelText('Description'), 'Verified source record');
    await user.type(screen.getByLabelText('Source / reference'), 'SRC-125');
    await user.click(screen.getByRole('button', { name: 'Confirm & Save' }));

    await waitFor(() => expect(mocks.accountingMutation).toHaveBeenCalledOnce());
    expect(mocks.accountingMutation).toHaveBeenCalledWith(
      ids.company,
      ids.user,
      path,
      'POST',
      expect.objectContaining({
        amount: '125.5',
        branch_id: ids.branch,
        category_id: categoryId,
        description: 'Verified source record',
        source_reference: 'SRC-125',
      }),
    );
    expect(invalidate).toHaveBeenCalledWith({ queryKey: queryKeys.accountingBase(ids.user, ids.company) });
    expect(onSuccess).toHaveBeenCalledOnce();
  });

  it('posts actual Receipt and Payment through distinct resources tied to their selected obligation', async () => {
    for (const { route, row, button, path } of [
      { route: 'Company Income', row: incomeRow, button: 'Record Receipt', path: 'receipts/' },
      { route: 'Company Expenses', row: expenseRow, button: 'Record Payment', path: 'payments/' },
    ]) {
      vi.clearAllMocks();
      mocks.accountingMutation.mockResolvedValue({ id: ids.income });
      const user = userEvent.setup();
      renderView(route);
      await openCurrentEvent(user, row);
      await user.clear(screen.getByLabelText('Actual amount (₹)'));
      await user.type(screen.getByLabelText('Actual amount (₹)'), '25.00');
      await user.selectOptions(screen.getByLabelText(route === 'Company Income' ? 'Income to receive against' : 'Expense to pay against'), row.id);
      await user.selectOptions(screen.getByLabelText('Cash / Bank account'), ids.cash);
      await user.selectOptions(screen.getByLabelText('Branch'), ids.branch);
      await user.clear(screen.getByLabelText('Description'));
      await user.type(screen.getByLabelText('Description'), 'Partial cash event');
      await user.clear(screen.getByLabelText('Receipt / payment reference'));
      await user.type(screen.getByLabelText('Receipt / payment reference'), `CASH-${row.source_reference}`);
      await user.click(screen.getByRole('button', { name: 'Confirm & Save' }));
      await waitFor(() => expect(mocks.accountingMutation).toHaveBeenCalledWith(
        ids.company,
        ids.user,
        path,
        'POST',
        expect.objectContaining({ amount: '25', target_event_id: row.id, account_id: ids.cash }),
      ));
    }
  });

  it.each([
    ['Opening balance', 'opening-balances/', async (user: ReturnType<typeof userEvent.setup>) => {
      await user.selectOptions(screen.getByLabelText('Cash / Bank account'), ids.cash);
      await user.type(screen.getByLabelText('Signed opening amount (₹)'), '-50.00');
      await user.selectOptions(screen.getByLabelText('Branch'), ids.branch);
      await user.type(screen.getByLabelText('Reason'), 'Opening correction');
      await user.type(screen.getByLabelText('Source / reference'), 'OPEN-1');
    }],
    ['Transfer', 'transfers/', async (user: ReturnType<typeof userEvent.setup>) => {
      await user.selectOptions(screen.getByLabelText('From account'), ids.cash);
      await user.selectOptions(screen.getByLabelText('To account'), ids.bank);
      await user.type(screen.getByLabelText('Transfer amount (₹)'), '20.00');
      await user.selectOptions(screen.getByLabelText('Branch'), ids.branch);
      await user.type(screen.getByLabelText('Reason'), 'Move funds');
      await user.type(screen.getByLabelText('Source / reference'), 'TR-1');
    }],
  ] as const)('posts %s through its specific API resource', async (button, path, fill) => {
    const user = userEvent.setup();
    renderView('Accounting');
    await openTools(user);
    await user.click(screen.getByRole('button', { name: button }));
    await fill(user);
    await user.click(screen.getByRole('button', { name: 'Confirm & Save' }));
    await waitFor(() => expect(mocks.accountingMutation).toHaveBeenCalledWith(
      ids.company,
      ids.user,
      path,
      'POST',
      expect.any(Object),
    ));
  });

  it.each([
    ['Add account', 'accounts/', async (user: ReturnType<typeof userEvent.setup>) => {
      await user.selectOptions(screen.getByLabelText('Account type'), 'BANK');
      await user.type(screen.getByLabelText('Name'), 'Reserve Bank');
    }],
    ['Add category', 'categories/', async (user: ReturnType<typeof userEvent.setup>) => {
      await user.selectOptions(screen.getByLabelText('Category type'), 'EXPENSE');
      await user.type(screen.getByLabelText('Name'), 'Utilities');
    }],
  ] as const)('posts %s to its backend resource', async (button, path, fill) => {
    const user = userEvent.setup();
    renderView('Accounting');
    await openTools(user);
    await user.click(screen.getByRole('button', { name: button }));
    await fill(user);
    await user.click(screen.getByRole('button', { name: 'Confirm & Save' }));
    await waitFor(() => expect(mocks.accountingMutation).toHaveBeenCalledWith(
      ids.company,
      ids.user,
      path,
      'POST',
      expect.any(Object),
    ));
  });

  it('offers both approved correction outcomes and sends only a selected valid outcome', async () => {
    const user = userEvent.setup();
    renderView('Company Income');
    await user.click(screen.getByRole('row', { name: `Open INCOME record ${incomeRow.source_reference}` }));
    await user.click(await screen.findByRole('button', { name: 'Correct' }));

    expect(screen.getByRole('radio', { name: /Reverse only/ })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Reverse and replace/ })).toBeInTheDocument();
    await user.click(screen.getByRole('radio', { name: /Reverse only/ }));
    await user.click(screen.getByRole('radio', { name: 'No' }));
    await user.type(screen.getByLabelText('Correction reason'), 'Duplicate entry');
    await user.click(screen.getByRole('button', { name: 'Confirm & Save' }));

    await waitFor(() => expect(mocks.accountingMutation).toHaveBeenCalledWith(
      ids.company,
      ids.user,
      `events/${ids.income}/corrections/`,
      'POST',
      expect.objectContaining({ outcome: 'REVERSE_ONLY', event_occurred: false, reason: 'Duplicate entry' }),
    ));
  });

  it.each(['INCOME', 'EXPENSE', 'RECEIPT', 'PAYMENT', 'OPENING_BALANCE', 'TRANSFER'] as const)(
    'offers both approved correction choices for %s records',
    async (eventType) => {
      const row = eventRow(eventType);
      mocks.useAccountingEvents.mockReturnValue({
        data: { count: 1, next: null, previous: null, results: [row] },
        isPending: false,
        isError: false,
      });
      mocks.useAccountingEvent.mockReturnValue({ data: eventDetail(row), isPending: false, isError: false });
      const user = userEvent.setup();
      renderView('Transactions');
      await user.click(screen.getByRole('row', { name: `Open ${eventType} record ${row.source_reference}` }));
      await user.click(await screen.findByRole('button', { name: 'Correct' }));

      expect(screen.getByRole('radio', { name: /Reverse only/ })).toBeInTheDocument();
      expect(screen.getByRole('radio', { name: /Reverse and replace/ })).toBeInTheDocument();
    },
  );

  it('keeps the form open and shows an error when the backend rejects the write', async () => {
    const user = userEvent.setup();
    mocks.accountingMutation.mockRejectedValue(new Error('Accounting request rejected.'));
    const { onSuccess } = renderView('Company Income');
    await user.click(screen.getByRole('button', { name: 'Record Income' }));
    await fillIncomeOrExpense(user);
    await user.click(screen.getByRole('button', { name: 'Confirm & Save' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Accounting request rejected.');
    expect(screen.getByRole('dialog', { name: 'Record Company Income' })).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('shows the Company-wide Branch option selected for a Company Accountant', async () => {
    const user = userEvent.setup();
    renderView('Company Income');
    await user.click(screen.getByRole('button', { name: 'Record Income' }));

    const branch = screen.getByLabelText('Branch') as HTMLSelectElement;
    expect(branch.selectedOptions[0]?.textContent).toBe('Company-wide');
  });
});
