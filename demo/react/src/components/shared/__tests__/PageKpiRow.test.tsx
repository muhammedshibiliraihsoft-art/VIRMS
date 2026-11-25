import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { PageKpiRow } from '../PageKpiRow';

it('does not present cached figures as current when the source is unavailable', () => {
  render(<PageKpiRow status="unavailable" items={[{ label: 'One', value: '42' }, { label: 'Two', value: '0' }, { label: 'Three', value: '7' }]} />);
  expect(screen.getAllByText('Unavailable')).toHaveLength(3);
  expect(screen.queryByText('42')).not.toBeInTheDocument();
  expect(screen.queryByText('0')).not.toBeInTheDocument();
});
