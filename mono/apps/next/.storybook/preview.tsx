import React from 'react';
import type { Preview } from '@storybook/react';
import '../app/globals.css';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    nextjs: {
      appDirectory: true,
    },
  },
  decorators: [
    (Story) => (
      <div style={{ padding: '2rem' }}>
        <Story />
      </div>
    ),
  ],
};

export default preview;

