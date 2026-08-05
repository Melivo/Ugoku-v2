import { loadAuthConfig } from "./auth.js";

export interface CrudItem {
  id: string;
  name: string;
  createdAt: string;
}

export interface CrudRepository {
  list(input: { limit: number; offset: number }): Promise<CrudItem[]>;
  get(id: string): Promise<CrudItem | null>;
  create(input: { name: string }): Promise<CrudItem>;
  update(id: string, input: { name: string }): Promise<CrudItem | null>;
  delete(id: string): Promise<boolean>;
}

export interface CrudServiceOptions {
  repository: CrudRepository;
}

export function createCrudService(options: CrudServiceOptions) {
  const { repository } = options;

  return {
    async list(input: { limit?: number; offset?: number }) {
      await requireAuth();
      const limit = clampLimit(input.limit ?? 50);
      const offset = Math.max(0, input.offset ?? 0);
      return repository.list({ limit, offset });
    },

    async get(id: string) {
      await requireAuth();
      assertId(id);
      return repository.get(id);
    },

    async create(input: { name?: unknown }) {
      await requireAuth();
      const name = parseName(input.name);
      return repository.create({ name });
    },

    async update(id: string, input: { name?: unknown }) {
      await requireAuth();
      assertId(id);
      const name = parseName(input.name);
      return repository.update(id, { name });
    },

    async delete(id: string) {
      await requireAuth();
      assertId(id);
      return repository.delete(id);
    },
  };
}

async function requireAuth(): Promise<void> {
  const auth = await loadAuthConfig();
  if (!auth.giteaToken) {
    throw new Error("No Gitea token configured.");
  }
}

function assertId(id: string): void {
  if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
    throw new Error("Invalid id.");
  }
}

function parseName(value: unknown): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error("Name is required.");
  }
  return value.trim();
}

function clampLimit(limit: number): number {
  return Math.min(Math.max(limit, 1), 100);
}
