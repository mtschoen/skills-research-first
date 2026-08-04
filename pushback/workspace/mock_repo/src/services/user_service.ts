export class UserService {
  validate(user: any): boolean {
    return user != null && user.id != null;
  }

  getById(id: string): any {
    return { id, name: 'stub' };
  }

  updateProfile(id: string, patch: any): void {
    // stub
  }
}
