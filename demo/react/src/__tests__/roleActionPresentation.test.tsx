import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from '../App';

describe('role-aware business action presentation', () => {
  it('hides prototype write actions from an Owner while keeping them for an Accountant', () => {
    const { rerender } = render(<App companyWideRoles={['owner']} />);

    expect(screen.queryByRole('button', { name: 'Record Receipt' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'New Sale' })).not.toBeInTheDocument();

    rerender(<App companyWideRoles={['accountant']} />);
    expect(screen.getByRole('button', { name: 'Record Receipt' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'New Sale' })).toBeInTheDocument();
  });
});
