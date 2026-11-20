import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Phase8ReadinessView } from '../Phase8ReadinessView';

describe('Phase8ReadinessView', () => {
  it('states that Investor settlement is not implemented without obsolete BDR policy claims', () => {
    render(<Phase8ReadinessView routeKey="Reconciliation & Settlement" />);
    expect(screen.getByRole('heading', { name: 'Investor reconciliation and settlement' })).toBeInTheDocument();
    expect(screen.getByText(/confirmed reconciliation and final settlement workflow is not yet implemented/i)).toBeInTheDocument();
    expect(screen.queryByText(/board ratification|shareholder consensus|BDR-/i)).not.toBeInTheDocument();
  });

  it('does not describe Accounting Result as distributable Company Profit', () => {
    render(<Phase8ReadinessView routeKey="Owner Distribution" />);
    expect(screen.getByText(/not the confirmed distributable Company Profit/i)).toBeInTheDocument();
    expect(screen.getByText(/No Owner distribution or Cash\/Bank movement is created/i)).toBeInTheDocument();
  });
});
