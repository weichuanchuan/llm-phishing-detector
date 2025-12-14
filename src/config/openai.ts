import OpenAI from 'openai';

/**
 * OpenAI client configuration
 * Uses the official OpenAI API
 */
export const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});
