import type { Snapshot } from "./types";
import snapshot from "../../public/data/snapshot.json";

/**
 * 빌드 타임에 굳혀둔 데이터를 그대로 import.
 * - Next.js가 정적 빌드 시 JSON을 번들에 포함 (~400KB pre-gzip)
 * - 클라이언트는 런타임에 fetch 없이 즉시 데이터 접근
 */
export const data: Snapshot = snapshot as Snapshot;
