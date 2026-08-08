/** UI-Erweiterungen aus Fallback-Schema mit Registry-Schema zusammenführen. */

type SchemaProperty = Record<string, unknown>;
type InputSchema = {
  title?: string;
  description?: string;
  properties?: Record<string, SchemaProperty>;
  required?: string[];
};

const UI_KEYS = ["x-widget", "x-visible-when", "x-enum-labels", "title", "description"] as const;

function mergeProperty(fallback: SchemaProperty, fromRegistry: SchemaProperty): SchemaProperty {
  const merged = { ...fromRegistry };
  for (const key of UI_KEYS) {
    if (fallback[key] !== undefined) {
      merged[key] = fallback[key];
    }
  }
  return merged;
}

export function mergeAgentInputSchema(
  fallback: InputSchema,
  fromRegistry: InputSchema,
): InputSchema {
  const fbProps = fallback.properties ?? {};
  const regProps = { ...(fromRegistry.properties ?? {}) };
  for (const [key, fbField] of Object.entries(fbProps)) {
    regProps[key] = mergeProperty(fbField, regProps[key] ?? fbField);
  }
  return {
    ...fromRegistry,
    title: fallback.title ?? fromRegistry.title,
    description: fallback.description ?? fromRegistry.description,
    properties: regProps,
  };
}
