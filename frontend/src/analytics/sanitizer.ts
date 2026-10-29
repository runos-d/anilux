import { eventCatalog, type AnalyticsEventMap, type AnalyticsEventName, type FieldRule } from "./catalog";

const forbiddenKey = /(?:^|_)(?:authorization|cookie|email|phone|nickname|user_?id|token|secret|password|message|comment|content|body|filename|file_name|query|search|fragment|hash|text)(?:_|$)/i;
const forbiddenValue = /(?:[?&#][^\s=]+=|bearer\s+|\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b|\b(?:\+?\d[\d\s().-]{7,}\d)\b)/i;
const safeCode = /^[a-z0-9][a-z0-9_.:-]{0,63}$/;
const safeRoute = /^\/[a-z0-9][a-z0-9/_-]{0,95}$/;

export class AnalyticsPayloadError extends Error {}

function hasForbiddenData(value: unknown, key = "", seen = new WeakSet<object>()): boolean {
  if (forbiddenKey.test(key)) return true;
  if (typeof value === "string") return forbiddenValue.test(value) || value.length > 128;
  if (!value || typeof value !== "object") return false;
  if (seen.has(value)) return true;
  seen.add(value);
  if (Array.isArray(value)) return value.some((item) => hasForbiddenData(item, key, seen));
  return Object.entries(value).some(([childKey, child]) => hasForbiddenData(child, childKey, seen));
}

function reject(message: string): null {
  if (import.meta.env.DEV || import.meta.env.MODE === "test") throw new AnalyticsPayloadError(message);
  return null;
}

export function sanitizeEvent<K extends AnalyticsEventName>(
  name: K,
  payload: AnalyticsEventMap[K],
): Readonly<Record<string, string | number | boolean>> | null {
  const rules = eventCatalog[name];
  if (!rules) return reject("Unknown analytics event");
  if (hasForbiddenData(payload)) return reject(`Forbidden analytics data in ${name}`);

  const source = payload as Record<string, unknown>;
  const allowedKeys = Object.keys(rules);
  if (Object.keys(source).some((key) => !allowedKeys.includes(key))) {
    return reject(`Unknown analytics field in ${name}`);
  }
  if (allowedKeys.some((key) => !(key in source))) return reject(`Missing analytics field in ${name}`);

  const clean: Record<string, string | number | boolean> = {};
  for (const [key, rule] of Object.entries(rules as Record<string, FieldRule>)) {
    const value = source[key];
    if (rule.type === "enum" && (typeof value !== "string" || !rule.values.includes(value))) {
      return reject(`Invalid analytics enum ${name}.${key}`);
    }
    if (rule.type === "integer" && (!Number.isInteger(value) || (value as number) < rule.min || (value as number) > rule.max)) {
      return reject(`Invalid analytics integer ${name}.${key}`);
    }
    if (rule.type === "safe_code" && (typeof value !== "string" || !safeCode.test(value))) {
      return reject(`Invalid analytics code ${name}.${key}`);
    }
    if (rule.type === "safe_route" && (typeof value !== "string" || !safeRoute.test(value))) {
      return reject(`Invalid analytics route ${name}.${key}`);
    }
    clean[key] = value as string | number | boolean;
  }
  return Object.freeze(clean);
}

export function isForbiddenAnalyticsValue(value: unknown): boolean {
  return hasForbiddenData(value);
}
