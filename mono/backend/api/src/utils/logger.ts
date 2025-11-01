/**
 * Winston logger configuration
 */
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, ...rest }) => {
          const meta = Object.keys(rest).length ? JSON.stringify(rest, null, 2) : '';
          return `${timestamp} [${level}]: ${message} ${meta}`;
        })
      ),
    }),
  ],
});
