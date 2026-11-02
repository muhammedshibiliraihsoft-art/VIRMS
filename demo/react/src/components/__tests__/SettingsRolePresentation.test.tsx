import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { initialData } from '../../data/mockData';
import { SettingsAdminView } from '../shared/SettingsAdminView';

describe('tenant Settings role presentation', () => {
  it('exposes appearance only, keeping Branch administration and demo-data controls out', () => {
    render(
      <SettingsAdminView
        initialTab="theme-appearance"
        data={initialData}
        currentThemePalette="default"
        onSelectThemePalette={vi.fn()}
        onUpdateData={vi.fn()}
        onOpenFormModal={vi.fn()}
        onSuccessMessage={vi.fn()}
        showNonThemeTabs={false}
      />
    );

    expect(screen.getByRole('heading', { name: 'Appearance & Theme' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Appearance & Theme' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Garages / Branches' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Demo Data & Seed' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Export Snapshot (JSON)' })).not.toBeInTheDocument();
  });
});
