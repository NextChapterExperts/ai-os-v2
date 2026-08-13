export type UserRole = "user" | "admin";

export interface AuthUser {
  username: string;
  name: string;
  role: UserRole;
  personId: string;
}

export const VALID_CREDENTIALS: Record<string, { pass: string; name: string; role: UserRole; personId: string }> = {
  peter: {
    pass: "peter",
    name: "Peter Alexander",
    role: "user",
    personId: "person:peter-alexander",
  },
  admin: {
    pass: "admin",
    name: "Administrator",
    role: "admin",
    personId: "person:admin",
  },
};

const AUTH_USER_KEY = "aios_auth_user";
const AUTH_ROLE_KEY = "aios_auth_role";

export function getStoredAuth(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const username = localStorage.getItem(AUTH_USER_KEY);
  const role = localStorage.getItem(AUTH_ROLE_KEY) as UserRole | null;
  if (!username || !role || !VALID_CREDENTIALS[username]) {
    return null;
  }
  const cred = VALID_CREDENTIALS[username];
  return {
    username,
    name: cred.name,
    role: cred.role,
    personId: cred.personId,
  };
}

export function loginUser(usernameInput: string, passwordInput: string): AuthUser | null {
  const username = usernameInput.trim().toLowerCase();
  const password = passwordInput.trim();

  const cred = VALID_CREDENTIALS[username];
  if (cred && cred.pass === password) {
    if (typeof window !== "undefined") {
      localStorage.setItem(AUTH_USER_KEY, username);
      localStorage.setItem(AUTH_ROLE_KEY, cred.role);
      localStorage.setItem("aios_active_user_id", cred.personId);
      localStorage.setItem("aios_active_user_name", cred.name);
      window.dispatchEvent(new CustomEvent("aios-auth-changed", { detail: { username, role: cred.role } }));
    }
    return {
      username,
      name: cred.name,
      role: cred.role,
      personId: cred.personId,
    };
  }
  return null;
}

export function logoutUser() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(AUTH_USER_KEY);
    localStorage.removeItem(AUTH_ROLE_KEY);
    window.dispatchEvent(new CustomEvent("aios-auth-changed", { detail: null }));
  }
}
