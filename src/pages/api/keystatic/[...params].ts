import { makeAPIRouteHandler } from '@keystatic/astro/api';
import keystaticConfig from '../../../../keystatic.config';

export const all = makeAPIRouteHandler({
  config: keystaticConfig,
});

export function getStaticPaths() {
  return [
    { params: { params: undefined } }
  ];
}
