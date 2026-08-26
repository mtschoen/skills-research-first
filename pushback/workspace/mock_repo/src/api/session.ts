import { UserService } from '../services/user_service';
import { LegacyAuth } from '../auth/legacy_auth';

const users = new UserService();

export function refreshSession(req: any, res: any) {
  const user = users.getById(req.session.userId);
  const migratedToken = LegacyAuth.migrateSessionToken(req.session.token);
  return res.json({ user, token: migratedToken });
}
