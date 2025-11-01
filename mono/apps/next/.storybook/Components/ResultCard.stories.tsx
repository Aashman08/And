import type { Meta, StoryObj } from '@storybook/react';
import { ResultCard } from '../../components/search/ResultCard';
import type { SearchResult, SummarySection } from '@/lib/api';

const meta: Meta<typeof ResultCard> = {
  title: 'Search/ResultCard',
  component: ResultCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ResultCard>;

const mockPaperResult: SearchResult = {
  id: 'paper-1',
  source: 'papers',
  title: 'Transformer Architecture for Large Language Models',
  snippet: 'We present a novel transformer architecture that scales efficiently to billions of parameters while maintaining high performance on downstream tasks.',
  score: 0.95,
  why_this_result: [
    'High relevance score matches your query about transformer architecture',
    'Recent publication from 2024',
    'Highly cited paper with 500+ citations',
  ],
  metadata: {
    year: 2024,
    venue: 'NeurIPS',
    authors: ['John Doe', 'Jane Smith', 'Bob Johnson'],
    concepts: ['Machine Learning', 'NLP', 'Deep Learning'],
    doi: '10.1234/example.doi',
  },
};

const mockStartupResult: SearchResult = {
  id: 'startup-1',
  source: 'startups',
  title: 'AI-Powered Drug Discovery Platform',
  snippet: 'Revolutionary platform using machine learning to accelerate drug discovery by predicting molecular interactions and drug efficacy.',
  score: 0.88,
  why_this_result: [
    'Matches your interest in AI and healthcare',
    'Series B funding stage indicates strong traction',
    'Active in the gene therapy space',
  ],
  metadata: {
    year: 2023,
    stage: 'Series B',
    industry: ['Healthcare', 'Biotech', 'AI'],
    website: 'https://example.com',
  },
};

const mockSummary: SummarySection = {
  problem: 'Traditional drug discovery is time-consuming and expensive, taking years to bring a drug to market.',
  approach: 'We use machine learning models trained on molecular data to predict drug-target interactions and efficacy.',
  evidence_or_signals: 'Series B funding of $50M, partnerships with 3 major pharma companies, 2 drugs in clinical trials.',
  result: 'Reduced drug discovery timeline from 5 years to 18 months, with 3x improvement in success rate.',
  limitations: 'Early stage validation, limited to specific molecular classes, requires large datasets for training.',
};

export const PaperResult: Story = {
  args: {
    result: mockPaperResult,
    onSummarize: () => {
      console.log('Summarizing paper...');
    },
    isSummarizing: false,
  },
  render: (args) => {
    return (
      <div className="w-full max-w-2xl">
        <ResultCard {...args} />
      </div>
    );
  },
};

export const StartupResult: Story = {
  args: {
    result: mockStartupResult,
    onSummarize: () => {
      console.log('Summarizing startup...');
    },
    isSummarizing: false,
  },
  render: (args) => {
    return (
      <div className="w-full max-w-2xl">
        <ResultCard {...args} />
      </div>
    );
  },
};

export const WithSummary: Story = {
  args: {
    result: mockStartupResult,
    summary: mockSummary,
    onSummarize: () => {
      console.log('Summarizing...');
    },
    isSummarizing: false,
  },
  render: (args) => {
    return (
      <div className="w-full max-w-2xl">
        <ResultCard {...args} />
      </div>
    );
  },
};

export const Summarizing: Story = {
  args: {
    result: mockPaperResult,
    onSummarize: () => {
      console.log('Summarizing...');
    },
    isSummarizing: true,
  },
  render: (args) => {
    return (
      <div className="w-full max-w-2xl">
        <ResultCard {...args} />
      </div>
    );
  },
};

