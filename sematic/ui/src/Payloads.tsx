import { Run, Artifact, Edge, Note, User } from "./Models";

export type RunListPayload = {
  current_page_url: string;
  next_page_url?: string;
  limit: number;
  next_cursor?: string;
  after_cursor_count: number;
  content: Run[];
};

export type RunViewPayload = {
  content: Run;
};

export type ArtifactMap = {
  input: Map<string, Artifact>;
  output: Map<string, Artifact>;
};

export type RunArtifactMap = Map<string, ArtifactMap>;

export type ArtifactListPayload = {
  content: Artifact[];
};

export type EdgeListPayload = {
  content: Edge[];
};

export type RunGraphPayload = {
  root_id: string;
  runs: Run[];
  edges: Edge[];
  artifacts: Artifact[];
};

export type NoteListPayload = {
  content: Note[];
  authors: User[];
};

export type NoteCreatePayload = {
  content: Note;
};

export type GoogleLoginPayload = {
  user: User;
};

export type AuthenticatePayload = {
  authenticate: boolean;
  providers: {
    GOOGLE_OAUTH_CLIENT_ID?: string;
    GITHUB_OAUTH_CLIENT_ID?: string;
  };
};

export type EnvPayload = {
  env: { [k: string]: string };
};
