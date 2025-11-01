import type { Meta, StoryObj } from '@storybook/react';
import { SearchBar } from '../../components/search/SearchBar';

const meta: Meta<typeof SearchBar> = {
  title: 'Search/SearchBar',
  component: SearchBar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof SearchBar>;

export const Default: Story = {
  args: {
    onSearch: (query: string) => {
      console.log('Search query:', query);
    },
    isSearching: false,
  },
};

export const Searching: Story = {
  args: {
    onSearch: (query: string) => {
      console.log('Search query:', query);
    },
    isSearching: true,
  },
};

export const WithInitialQuery: Story = {
  args: {
    onSearch: (query: string) => {
      console.log('Search query:', query);
    },
    isSearching: false,
  },
  render: (args) => {
    return (
      <div className="w-full max-w-3xl">
        <SearchBar {...args} />
      </div>
    );
  },
};

