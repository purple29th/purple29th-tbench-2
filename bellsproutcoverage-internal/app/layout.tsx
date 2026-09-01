import './globals.css';
import type { ReactNode } from 'react';
// import { InternAuthOIDCProvider } from '@nest/intern-auth'; // Uncomment in real Nest fbsource build
// import { XDSProvider } from '@nest/xds';

export const metadata = {
  title: 'BellsproutCoverage — Internal',
  description: 'Team coverage dashboard — internal only (Nest, device cert required)',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* In fbsource, wrap with InternAuthOIDCProvider + XDSProvider for real SSO + design system */}
        {/* <InternAuthOIDCProvider><XDSProvider>{children}</XDSProvider></InternAuthOIDCProvider> */}
        {children}
      </body>
    </html>
  );
}
