import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { InvestorUtilizationCard } from '../InvestorUtilizationCard';

it('does not show a cached utilization bar when the fund request fails', () => {
  const { container } = render(<InvestorUtilizationCard totalUsed={50} availableAmount={50} hasError />);
  expect(screen.getAllByText('Unavailable')).toHaveLength(2);
  expect(container.querySelector('[style="width: 0%;"]')).not.toBeNull();
});

it('includes held reserve in the fund utilization denominator', () => {
  const { container } = render(<InvestorUtilizationCard totalUsed={25} availableAmount={50} reservedAmount={25} />);
  expect(container.querySelector('[style="width: 25%;"]')).not.toBeNull();
});
