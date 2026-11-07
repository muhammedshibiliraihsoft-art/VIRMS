import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RolePresentationProvider } from '../../../auth/RolePresentationContext';
import { initialData } from '../../../data/mockData';
import { SharedFormModal } from '../SharedFormModal';

describe.each(['companyExpense', 'otherIncome'] as const)('%s legacy form', (type) => {
  it('does not mutate prototype data or report success', () => {
    const onUpdateData = vi.fn();
    const onSuccessMessage = vi.fn();
    const onClose = vi.fn();
    const { container } = render(
      <RolePresentationProvider companyWideRoles={['accountant']}>
        <SharedFormModal
          isOpen
          type={type}
          onClose={onClose}
          data={initialData}
          onUpdateData={onUpdateData}
          onSuccessMessage={onSuccessMessage}
        />
      </RolePresentationProvider>
    );

    fireEvent.submit(container.querySelector('form')!);

    expect(screen.getByText(/This legacy form is not connected to Company Accounting/)).toBeInTheDocument();
    expect(onUpdateData).not.toHaveBeenCalled();
    expect(onSuccessMessage).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });
});
