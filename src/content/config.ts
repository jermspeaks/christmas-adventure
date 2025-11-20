import { defineCollection, z } from 'astro:content';

const sectionsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    id: z.string(),
    title: z.string(),
    choices: z.array(
      z.object({
        text: z.string(),
        target: z.string(), // e.g., "section-2.md"
      })
    ).optional(),
  }),
});

export const collections = {
  'sections': sectionsCollection,
};

