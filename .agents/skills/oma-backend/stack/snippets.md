# TypeScript Node CLI Snippets

## Route/Handler + Auth Example

```ts
import { loadAuthConfig } from "./auth.js";

export async function runSecureCommand(options: {
  workspacePath: string;
}): Promise<{ success: boolean; message: string }> {
  const auth = await loadAuthConfig();
  if (!auth.giteaToken) {
    return {
      success: false,
      message: "No Gitea token configured. Run 'pros auth token set --stdin' first.",
    };
  }

  return {
    success: true,
    message: `Workspace ready: ${options.workspacePath}`,
  };
}
```

## Validation Schema Example

```ts
interface InstallerState {
  installedVersion: string;
  releaseTag: string;
}

export function parseInstallerState(input: unknown): InstallerState {
  if (!input || typeof input !== "object") {
    throw new Error("Installer state must be an object.");
  }

  const state = input as Record<string, unknown>;
  if (typeof state.installedVersion !== "string") {
    throw new Error("Installer state is missing installedVersion.");
  }
  if (typeof state.releaseTag !== "string") {
    throw new Error("Installer state is missing releaseTag.");
  }

  return {
    installedVersion: state.installedVersion,
    releaseTag: state.releaseTag,
  };
}
```

## ORM Model/Entity Example

No ORM is used. Model persisted file state with TypeScript interfaces and serialize explicitly.

```ts
export interface ProsConfigFile {
  version: string;
  runtimeName: "pros";
}
```

## DI (Dependency Injection) Example

```ts
import type { FileSystemLike } from "./contracts.js";

export interface WorkspaceServiceDeps {
  fileSystem: FileSystemLike;
  now: () => Date;
}

export function createWorkspaceService(deps: WorkspaceServiceDeps) {
  return {
    async statWorkspace(path: string) {
      const stat = await deps.fileSystem.stat(path);
      return {
        path,
        isDirectory: stat.isDirectory(),
        checkedAt: deps.now().toISOString(),
      };
    },
  };
}
```

## Repository Pattern Example

```ts
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

export interface StateRepository<T> {
  read(): Promise<T | null>;
  write(value: T): Promise<void>;
}

export function jsonFileRepository<T>(filePath: string): StateRepository<T> {
  return {
    async read() {
      try {
        return JSON.parse(await readFile(filePath, "utf-8")) as T;
      } catch {
        return null;
      }
    },
    async write(value) {
      await mkdir(path.dirname(filePath), { recursive: true });
      await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`);
    },
  };
}
```

## Paginated Query Example

```ts
export async function fetchAllPages<T>(
  fetchPage: (page: number) => Promise<T[]>,
): Promise<T[]> {
  const results: T[] = [];

  for (let page = 1; ; page += 1) {
    const items = await fetchPage(page);
    if (items.length === 0) {
      break;
    }
    results.push(...items);
  }

  return results;
}
```

## Migration Example

No migration framework is used. Apply file-format migrations as explicit functions.

```ts
interface StateV1 {
  version: string;
}

interface StateV2 {
  installedVersion: string;
  migratedAt: string;
}

export function migrateState(input: StateV1 | StateV2): StateV2 {
  if ("installedVersion" in input) {
    return input;
  }

  return {
    installedVersion: input.version,
    migratedAt: new Date().toISOString(),
  };
}
```

## Test Example

```ts
import { describe, expect, it } from "vitest";
import { parseInstallerState } from "./state.js";

describe("parseInstallerState", () => {
  it("rejects invalid state", () => {
    expect(() => parseInstallerState({ releaseTag: "pros-v1.0.0" })).toThrow(
      "installedVersion",
    );
  });
});
```
