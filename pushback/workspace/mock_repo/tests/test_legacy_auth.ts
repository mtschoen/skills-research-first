import { LegacyAuth } from '../src/auth/legacy_auth';

describe('LegacyAuth', () => {
  it('validates a legacy cookie', () => {
    expect(LegacyAuth.validateLegacyCookie('legacy-abc')).toBe(true);
  });

  it('migrates a session token', () => {
    expect(LegacyAuth.migrateSessionToken('old')).toBe('migrated:old');
  });
});
