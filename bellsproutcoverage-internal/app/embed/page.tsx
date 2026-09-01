/**
 * /embed route — OUTSIDE (authenticated) group for Unidash iframe embedding.
 * Same content as main page but no CAT auth (publicRoutes in proxy.ts).
 * Required headers: X-Frame-Options SAMEORIGIN, CSP frame-ancestors *.facebook.com *.internalfb.com *.intern.facebook.com
 * See HOTD Embedding Hatch Dashboards into Unidash: https://fb.workplace.com/groups/hack.of.the.day/permalink/31221603950794822/
 * Landmine: CAT minting fails in cross-origin iframe → 405/No Data. Fix: custom /api/graphql using @nest/thrift-proxy fallback to server-identity.
 */
import MainPage from '../page';

export default function EmbedPage() {
  return <MainPage isEmbed />;
}
