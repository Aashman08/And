import type { Meta, StoryObj } from '@storybook/react';
import { Facets } from '../../components/search/Facets';
import type { SearchFilters } from '@/lib/api';

const meta: Meta<typeof Facets> = {
  title: 'Search/Facets',
  component: Facets,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Facets>;

export const Default: Story = {
  args: {
    filters: {},
    onFilterChange: (filters: SearchFilters) => {
      console.log('Filters changed:', filters);
    },
  },
  render: (args) => {
    return (
      <div className="w-64">
        <Facets {...args} />
      </div>
    );
  },
};

export const WithSourceFilter: Story = {
  args: {
    filters: {
      source: ['papers'],
    },
    onFilterChange: (filters: SearchFilters) => {
      console.log('Filters changed:', filters);
    },
  },
  render: (args) => {
    return (
      <div className="w-64">
        <Facets {...args} />
      </div>
    );
  },
};

export const WithAllFilters: Story = {
  args: {
    filters: {
      source: ['papers', 'startups'],
      year_gte: 2023,
    },
    onFilterChange: (filters: SearchFilters) => {
      console.log('Filters changed:', filters);
    },
  },
  render: (args) => {
    return (
      <div className="w-64">
        <Facets {...args} />
      </div>
    );
  },
};

