import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DemoBadge } from '../DemoBadge';

describe('DemoBadge', () => {
  it('labels demo-only data and actions accessibly', () => {
    render(<DemoBadge />);

    expect(screen.getByRole('note', { name: /not connected to the backend/i })).toHaveTextContent('Demo');
  });
});
