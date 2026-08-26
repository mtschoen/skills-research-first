export class LegacyAuth {
  static migrateSessionToken(oldToken: string): string {
    return `migrated:${oldToken}`;
  }

  static validateLegacyCookie(cookie: string): boolean {
    return cookie.startsWith('legacy-');
  }
}
