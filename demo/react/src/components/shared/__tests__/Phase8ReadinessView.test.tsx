import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Phase8ReadinessView } from '../Phase8ReadinessView';

describe('Phase8ReadinessView', () => {
  it('describes the current Investor settlement workflow without obsolete BDR policy claims', () => {
    render(<Phase8ReadinessView routeKey="Reconciliation & Settlement" />);
    expect(screen.getByRole('heading', { name: 'Investor reconciliation and settlement' })).toBeInTheDocument();
    expect(screen.getByText(/current confirmed positions and recorded Accounting movements/i)).toBeInTheDocument();
    expect(screen.queryByText(/board ratification|shareholder consensus|BDR-/i)).not.toBeInTheDocument();
  });

  it('describes confirmed Company period distribution instead of a placeholder', () => {
    render(<Phase8ReadinessView routeKey="Owner Distribution" />);
    expect(screen.getByText(/Accountant must confirm liabilities, carryforward and the distributable amount/i)).toBeInTheDocument();
    expect(screen.getByText(/Partial Owner payouts require a current confirmation/i)).toBeInTheDocument();
  });
});
