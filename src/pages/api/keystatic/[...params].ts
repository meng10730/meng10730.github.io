import { makeHandler } from '@keystatic/astro/api';
import keystaticConfig from '../../../../keystatic.config';

export const all = makeHandler({
  config: keystaticConfig,
});

export function getStaticPaths() {
  return [
    { params: { params: undefined } }
  ];
}
