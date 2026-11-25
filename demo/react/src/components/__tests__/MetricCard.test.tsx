import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MetricGrid } from '../MetricCard';

describe('dashboard metric states', () => {
  it('shows zero for successful empty counts and keeps a failed source unavailable', () => {
    render(<MetricGrid vehicleCount={0} soldVehicleCount={0} buyerReceivable={0} openJobsCount={null} vehiclesLoading={false} vehiclesError={false} garageLoading={false} garageError />);
    expect(screen.getAllByText('0')).toHaveLength(2);
    expect(screen.getByText('₹0')).toBeInTheDocument();
    expect(screen.getByText('Unavailable')).toBeInTheDocument();
  });
});
