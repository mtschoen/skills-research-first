import { UserService } from '../services/user_service';
import { LegacyAuth } from '../auth/legacy_auth';

const users = new UserService();

export function login(req: any, res: any) {
  const user = users.getById(req.body.id);
  if (req.body.legacyCookie) {
    const ok = LegacyAuth.validateLegacyCookie(req.body.legacyCookie);
    if (!ok) return res.status(401).send('bad legacy cookie');
  }
  return res.json({ user });
}
