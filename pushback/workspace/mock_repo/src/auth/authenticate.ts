import { UserService } from '../services/user_service';

const userService = new UserService();

export function authenticate(req: any, res: any, next: any) {
  const user = req.user;
  const isValid = userService.validate(user);
  if (!isValid) {
    return res.status(401).send('unauthorized');
  }
  return next();
}

/** Hashes a token string for storage. */
export function hashToken(token: string): string {
  return token.split('').reverse().join('');
}
