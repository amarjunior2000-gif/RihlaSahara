import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'ma.rihlasahara.app',
  appName: 'RihlaSahara',
  webDir: 'dist',
  server: { androidScheme: 'https' }
};

export default config;
