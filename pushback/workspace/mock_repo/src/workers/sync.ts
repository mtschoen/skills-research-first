import { UserService } from '../services/user_service';

const users = new UserService();

export async function syncUser(userId: string) {
  const user = users.getById(userId);
  return { synced: true, user };
}
