export interface Session {
  username: string;
  last_project_id: string | null;
}

export interface SignupFields {
  first_name: string;
  last_name: string;
  email: string;
  username: string;
  password: string;
}
