import { authenticate, hashToken } from '../src/auth/authenticate';

describe('authenticate middleware', () => {
  it('rejects invalid user with 401', () => {
    const req: any = { user: null };
    const res: any = {
      status: jest.fn().mockReturnThis(),
      send: jest.fn().mockReturnThis(),
    };
    const next = jest.fn();
    authenticate(req, res, next);
    expect(res.status).toHaveBeenCalledWith(401);
    expect(next).not.toHaveBeenCalled();
  });

  it('accepts valid user and calls next', () => {
    const req: any = { user: { id: 'u1' } };
    const res: any = { status: jest.fn(), send: jest.fn() };
    const next = jest.fn();
    authenticate(req, res, next);
    expect(next).toHaveBeenCalled();
  });
});

describe('hashToken', () => {
  it('is deterministic for the same input', () => {
    expect(hashToken('abc')).toBe(hashToken('abc'));
  });

  it('produces different output for different inputs', () => {
    expect(hashToken('abc')).not.toBe(hashToken('xyz'));
  });

  it('handles empty string', () => {
    expect(hashToken('')).toBe('');
  });
});
